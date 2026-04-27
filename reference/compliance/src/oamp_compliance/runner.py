"""OAMP Compliance Test Suite — main runner and CLI.

Usage:
    oamp-compliance --url http://localhost:8000
    oamp-compliance --url http://localhost:8000 --category must
    oamp-compliance --url http://localhost:8000 --format json
    oamp-compliance --url http://localhost:8000 --header "Authorization: Bearer $TOKEN"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Any

from .client import OAMPClient
from .reporter import generate_report
from .tests import must, should, functional  # noqa: F401 — triggers registry
from .tests.utils import TestResult, registry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OAMP Compliance Test Suite — verify any OAMP backend against the spec",
    )
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="Base URL of the OAMP server (e.g. http://localhost:8000)",
    )
    parser.add_argument(
        "--category", "-c",
        choices=["must", "should", "func", "all"],
        default="all",
        help="Test category to run (default: all)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json", "markdown", "junit"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--header", "-H",
        action="append",
        dest="headers",
        help="Additional HTTP headers (e.g. -H 'Authorization: Bearer $TOKEN')",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write report to file instead of stdout",
    )
    args = parser.parse_args()

    # Parse headers
    headers: dict[str, str] = {}
    if args.headers:
        for h in args.headers:
            if ":" in h:
                key, value = h.split(":", 1)
                headers[key.strip()] = value.strip()

    # Create client
    print(f"Connecting to {args.url}...", file=sys.stderr)
    client = OAMPClient(base_url=args.url, headers=headers, timeout=args.timeout)

    # Health check
    try:
        health = client.health_check()
        if health.status_code != 200:
            print(f"❌ Server health check failed: {health.status_code}", file=sys.stderr)
            sys.exit(1)
        print(f"✅ Server is reachable at {args.url}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Cannot connect to {args.url}: {e}", file=sys.stderr)
        sys.exit(1)

    # Collect tests
    all_tests = registry.get_all()
    if args.category != "all":
        all_tests = registry.get_by_category(args.category)

    if not all_tests:
        print(f"No tests found for category: {args.category}", file=sys.stderr)
        sys.exit(1)

    # Run tests
    results: list[TestResult] = []
    print(f"Running {len(all_tests)} tests...\n", file=sys.stderr)

    for category, test_id, description, test_fn in all_tests:
        try:
            result = test_fn(client)
        except Exception as e:
            result = TestResult(test_id, description, TestResult.FAIL, str(e))

        results.append(result)
        print(f"  {result}", file=sys.stderr)

    # Generate report
    report = generate_report(results, args.url, output_format=args.format)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\nReport written to {args.output}", file=sys.stderr)
    else:
        print("\n" + "=" * 60, file=sys.stderr)
        print(report)

    # Exit with non-zero if any tests failed
    failed = [r for r in results if r.status == TestResult.FAIL]
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()