#!/usr/bin/env python3
"""Translate OAMP spec markdown to ja/zh/ko/ms via OpenAI.

Loops over every spec version under spec/, finds the canonical English
source (prefers oamp-v{N}.md, falls back to oamp-v{N}-draft.md), and
translates each to the four target languages. Outputs land alongside
the source as oamp-v{N}.{lang}.md (always stripping -draft from the
output filename so dthink.ai's content paths stay stable).

A translation is only regenerated if it is missing or older (per git
log) than its source. This keeps re-runs cheap and produces minimal
PRs.

Designed to be invoked from the auto-translate-spec.yml workflow with
OPENAI_API_KEY in env.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI


LANGS = {
    "ja": "Japanese",
    "zh": "Chinese (Simplified)",
    "ko": "Korean",
    "ms": "Bahasa Melayu",
}

SYSTEM_PROMPT = (
    "You are a technical translator for an IETF-style protocol "
    "specification. Translate the following markdown document into "
    "{language}. Preserve all markdown formatting, code blocks, JSON "
    "examples, file paths, URLs, and identifiers exactly as they appear. "
    "Keep RFC 2119 keywords (MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, "
    "SHOULD, SHOULD NOT, RECOMMENDED, MAY, OPTIONAL) in English. Translate "
    "prose, headings, table cells, and prose comments only. Do not add "
    "translator notes or commentary."
)

# Each tuple is (version_dir_relative_to_repo, source_base, output_stem).
# source_base is the filename without .md or -draft.md.
# output_stem is what the translated files are named (without .{lang}.md).
TARGETS = [
    ("spec/v1", "oamp-v1", "oamp-v1"),
    ("spec/v1.1", "oamp-v1.1", "oamp-v1.1"),
    ("spec/v1.2", "oamp-v1.2", "oamp-v1.2"),
    ("spec/v1.2", "oamp-v1.2-governed-memory", "oamp-v1.2-governed-memory"),
    ("spec/v1.3", "oamp-v1.3", "oamp-v1.3"),
]


def find_source(version_dir: Path, base: str) -> Path | None:
    stable = version_dir / f"{base}.md"
    if stable.exists():
        return stable
    draft = version_dir / f"{base}-draft.md"
    if draft.exists():
        return draft
    return None


def git_commit_time(path: Path, repo: Path) -> int | None:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", str(path.relative_to(repo))],
            cwd=repo,
            text=True,
        ).strip()
        return int(out) if out else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def needs_update(source: Path, translated: Path, repo: Path) -> bool:
    if not translated.exists():
        return True
    src_t = git_commit_time(source, repo)
    tx_t = git_commit_time(translated, repo)
    if src_t is None or tx_t is None:
        return True
    return src_t > tx_t


def translate(client: OpenAI, source_text: str, language: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(language=language)},
            {"role": "user", "content": source_text},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    repo = Path(__file__).resolve().parents[1]

    updated = 0
    skipped = 0
    missing = 0

    for rel_dir, source_base, output_stem in TARGETS:
        version_dir = repo / rel_dir
        source = find_source(version_dir, source_base)
        if source is None:
            print(f"skip: no source in {rel_dir} for {source_base}")
            missing += 1
            continue

        try:
            source_text = source.read_text()
        except OSError as exc:
            print(f"ERROR: cannot read {source}: {exc}", file=sys.stderr)
            return 1

        for code, name in LANGS.items():
            out = version_dir / f"{output_stem}.{code}.md"
            if not needs_update(source, out, repo):
                print(f"skip: {out.relative_to(repo)} up-to-date")
                skipped += 1
                continue

            print(f"translate: {source.relative_to(repo)} -> {out.relative_to(repo)} ({name})")
            try:
                translated = translate(client, source_text, name)
            except Exception as exc:  # noqa: BLE001 — surface any API error
                print(f"ERROR: OpenAI call failed for {out}: {exc}", file=sys.stderr)
                return 1

            out.write_text(translated)
            updated += 1

    print(f"done: {updated} updated, {skipped} skipped, {missing} missing source(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
