#!/usr/bin/env bash
# Governed-memory canary round-trip for OAMP v1.2 interop matrix (#18).
#
# Pushes the canonical interop fixture through a producer -> consumer pair,
# then verifies that governance and provenance fields survive the round-trip
# (or that any losses are honestly advertised in /v1/capabilities).
#
# Usage:
#   scripts/interop-roundtrip.sh \
#     --producer-url https://producer.example \
#     --consumer-url https://consumer.example \
#     [--producer-token TOKEN] [--consumer-token TOKEN] \
#     [--user-id user-alice-123] \
#     [--fixture spec/v1.2/examples/knowledge-store-interop.json] \
#     [--out-dir ./interop-out]

set -euo pipefail

PRODUCER_URL=""
CONSUMER_URL=""
PRODUCER_TOKEN="${OAMP_PRODUCER_TOKEN:-}"
CONSUMER_TOKEN="${OAMP_CONSUMER_TOKEN:-}"
USER_ID="user-alice-123"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE="$REPO_ROOT/spec/v1.2/examples/knowledge-store-interop.json"
OUT_DIR="$REPO_ROOT/interop-out"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --producer-url)   PRODUCER_URL="$2"; shift 2 ;;
    --consumer-url)   CONSUMER_URL="$2"; shift 2 ;;
    --producer-token) PRODUCER_TOKEN="$2"; shift 2 ;;
    --consumer-token) CONSUMER_TOKEN="$2"; shift 2 ;;
    --user-id)        USER_ID="$2"; shift 2 ;;
    --fixture)        FIXTURE="$2"; shift 2 ;;
    --out-dir)        OUT_DIR="$2"; shift 2 ;;
    -h|--help)        sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$PRODUCER_URL" && -n "$CONSUMER_URL" ]] || {
  echo "error: --producer-url and --consumer-url are required" >&2
  exit 2
}
[[ -f "$FIXTURE" ]] || { echo "error: fixture not found: $FIXTURE" >&2; exit 2; }
command -v jq >/dev/null || { echo "error: jq is required" >&2; exit 2; }

mkdir -p "$OUT_DIR"
PRODUCER_EXPORT="$OUT_DIR/producer-export.json"
CONSUMER_EXPORT="$OUT_DIR/consumer-export.json"
PRODUCER_CAPS="$OUT_DIR/producer-capabilities.json"
CONSUMER_CAPS="$OUT_DIR/consumer-capabilities.json"
DIFF_REPORT="$OUT_DIR/diff-report.txt"
: > "$DIFF_REPORT"

say() { printf '\n=== %s ===\n' "$*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }
auth_header() { [[ -n "$1" ]] && echo "Authorization: Bearer $1" || echo ""; }

# Wraps curl so HTTP >= 400 fails the script and the body lands on stdout.
http() {
  local method="$1" url="$2" token="$3" body="${4:-}"
  local hdr; hdr="$(auth_header "$token")"
  local args=(-sS -X "$method" "$url" -H 'Content-Type: application/json' -H 'Accept: application/json' -w '\n%{http_code}')
  [[ -n "$hdr" ]] && args+=(-H "$hdr")
  [[ -n "$body" ]] && args+=(--data-binary "@$body")
  local raw; raw="$(curl "${args[@]}")"
  local code="${raw##*$'\n'}"; local payload="${raw%$'\n'*}"
  if [[ "$code" -ge 400 ]]; then
    echo "$payload" >&2
    fail "HTTP $code from $method $url"
  fi
  echo "$payload"
}

# 1. Validate fixture locally.
say "Step 1: validate fixture"
jq empty "$FIXTURE"
jq -e '.type == "knowledge_store" and (.entries | length) >= 3' "$FIXTURE" >/dev/null \
  || fail "fixture is not a knowledge_store with >=3 entries"
echo "fixture OK: $FIXTURE"

# 2-3. Import fixture into producer, then export.
say "Step 2: import fixture into producer"
http POST "$PRODUCER_URL/v1/import" "$PRODUCER_TOKEN" "$FIXTURE" >/dev/null
say "Step 3: export from producer"
echo "{\"user_id\":\"$USER_ID\"}" > "$OUT_DIR/_export-req.json"
http POST "$PRODUCER_URL/v1/export" "$PRODUCER_TOKEN" "$OUT_DIR/_export-req.json" > "$PRODUCER_EXPORT"
jq -e '.entries | length >= 3' "$PRODUCER_EXPORT" >/dev/null \
  || fail "producer export missing entries"

# 4-5. Import producer export into consumer, then export.
say "Step 4: import producer export into consumer"
http POST "$CONSUMER_URL/v1/import" "$CONSUMER_TOKEN" "$PRODUCER_EXPORT" >/dev/null
say "Step 5: export from consumer"
http POST "$CONSUMER_URL/v1/export" "$CONSUMER_TOKEN" "$OUT_DIR/_export-req.json" > "$CONSUMER_EXPORT"

# 6. Capabilities discovery on both backends.
say "Step 6: read /v1/capabilities from both backends"
http GET "$PRODUCER_URL/v1/capabilities" "$PRODUCER_TOKEN" > "$PRODUCER_CAPS"
http GET "$CONSUMER_URL/v1/capabilities" "$CONSUMER_TOKEN" > "$CONSUMER_CAPS"

# 7. Diff governance and provenance per entry id.
#    The fixture pins entry ids, so we compare keyed maps rather than arrays
#    (order is not guaranteed across backends).
say "Step 7: diff governance and provenance per entry id"
extract='
  .entries
  | map({
      id: .id,
      oamp_version: .oamp_version,
      governance: (.governance // null),
      provenance: (.provenance // null)
    })
  | sort_by(.id)
'
jq "$extract" "$PRODUCER_EXPORT" > "$OUT_DIR/_producer-fields.json"
jq "$extract" "$CONSUMER_EXPORT" > "$OUT_DIR/_consumer-fields.json"

if diff -u "$OUT_DIR/_producer-fields.json" "$OUT_DIR/_consumer-fields.json" > "$DIFF_REPORT"; then
  echo "no governance/provenance drift between producer and consumer"
  DRIFT=0
else
  echo "drift detected (see $DIFF_REPORT)"
  DRIFT=1
fi

# 8. If drift, cross-check against consumer capabilities. A drop is acceptable
#    only if the consumer explicitly advertises that gap.
if [[ "$DRIFT" -eq 1 ]]; then
  say "Step 8: reconcile drift against consumer capabilities"
  governance_jq='(.capabilities.governance // .governance // {})'
  caps_supports() { jq -e --arg k "$1" --argjson empty '{}' "
    ${governance_jq} as \$g
    | (\$g.supported // false) as \$supported
    | (\$g[\$k] // null) as \$value
    | (\$supported == true) and (\$value == true)
  " "$CONSUMER_CAPS" >/dev/null; }

  # Fields the script knows how to interpret.
  declare -A field_cap=(
    [governance.sensitivity_class]="supported"
    [governance.labels]="labels_supported"
    [governance.handling]="handling_supported"
    [provenance.sources]="extended_provenance_supported"
    [provenance.derived]="extended_provenance_supported"
  )

  unexplained=0
  for field in "${!field_cap[@]}"; do
    if grep -q -- "-.*\"${field#*.}\"" "$DIFF_REPORT" && \
       ! grep -q -- "+.*\"${field#*.}\"" "$DIFF_REPORT"; then
      cap_key="${field_cap[$field]}"
      if [[ "$cap_key" == "supported" ]]; then
        if jq -e "${governance_jq} | (.supported // false) == false" "$CONSUMER_CAPS" >/dev/null; then
          echo "  ok: $field dropped, consumer advertises governance.supported=false"
        else
          echo "  unexplained: $field dropped but consumer claims governance support"
          unexplained=1
        fi
      else
        if caps_supports "$cap_key"; then
          echo "  unexplained: $field dropped but consumer advertises $cap_key=true"
          unexplained=1
        else
          echo "  ok: $field dropped, consumer advertises $cap_key=false (documented lossy)"
        fi
      fi
    fi
  done

  if [[ "$unexplained" -eq 1 ]]; then
    fail "consumer dropped fields it advertises as supported (see $DIFF_REPORT and $CONSUMER_CAPS)"
  fi
fi

# 9. Pass.
say "Result"
echo "PASS  producer=$PRODUCER_URL  consumer=$CONSUMER_URL"
echo "artifacts in $OUT_DIR/"
