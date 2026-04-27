"""Report generator for compliance test results.

Supports JSON, Markdown, and JUnit XML output formats.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .tests.utils import TestResult


def generate_report(
    results: list[TestResult],
    server_url: str,
    output_format: str = "text",
) -> str:
    """Generate a compliance report in the specified format."""
    if output_format == "json":
        return _generate_json(results, server_url)
    elif output_format == "markdown":
        return _generate_markdown(results, server_url)
    elif output_format == "junit":
        return _generate_junit(results, server_url)
    else:
        return _generate_text(results, server_url)


def _summarize(results: list[TestResult]) -> dict[str, int]:
    summary = {"total": len(results), "passed": 0, "failed": 0, "skipped": 0}
    for r in results:
        if r.status == TestResult.PASS:
            summary["passed"] += 1
        elif r.status == TestResult.FAIL:
            summary["failed"] += 1
        elif r.status == TestResult.SKIP:
            summary["skipped"] += 1
    return summary


def _generate_text(results: list[TestResult], server_url: str) -> str:
    summary = _summarize(results)
    lines = [
        "=" * 60,
        f"OAMP v1.0.0 Compliance Report",
        f"Server: {server_url}",
        f"Date: {datetime.now(timezone.utc).isoformat()}",
        "=" * 60,
        "",
    ]

    categories: dict[str, list[TestResult]] = {}
    for r in results:
        categories.setdefault(r.test_id.split("-")[0], []).append(r)

    for cat_name, cat_results in sorted(categories.items()):
        cat_label = {"MUST": "MUST Requirements", "SHOULD": "SHOULD Requirements", "FUNC": "Functional Tests"}.get(
            cat_name, f"{cat_name} Tests"
        )
        lines.append(f"\n{cat_label}:")
        for r in cat_results:
            icon = {"PASS": "  ✅", "FAIL": "  ❌", "SKIP": "  ⚠️"}.get(r.status, "  ?")
            msg = f" -- {r.message}" if r.message else ""
            lines.append(f"{icon} {r.test_id}: {r.description}{msg}")

    lines.extend([
        "",
        "-" * 60,
        f"Result: {summary['passed']}/{summary['total']} passed, "
        f"{summary['failed']} failed, {summary['skipped']} skipped",
    ])

    if summary["failed"] > 0:
        lines.append("STATUS: NON-COMPLIANT")
    elif summary["skipped"] > 0:
        lines.append("STATUS: COMPLIANT (with skipped tests)")
    else:
        lines.append("STATUS: COMPLIANT")

    return "\n".join(lines)


def _generate_json(results: list[TestResult], server_url: str) -> str:
    summary = _summarize(results)
    report: dict[str, Any] = {
        "oamp_version": "1.0.0",
        "server_url": server_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "compliant": summary["failed"] == 0,
        "results": [r.to_dict() for r in results],
    }
    return json.dumps(report, indent=2)


def _generate_markdown(results: list[TestResult], server_url: str) -> str:
    summary = _summarize(results)
    lines = [
        f"# OAMP v1.0.0 Compliance Report",
        f"",
        f"**Server**: {server_url}",
        f"**Date**: {datetime.now(timezone.utc).isoformat()}",
        f"",
        f"## Summary",
        f"",
        f"| Status | Count |",
        f"|--------|-------|",
        f"| Passed | {summary['passed']} |",
        f"| Failed | {summary['failed']} |",
        f"| Skipped | {summary['skipped']} |",
        f"| **Total** | **{summary['total']}** |",
        f"",
        f"## Results",
        f"",
    ]

    categories: dict[str, list[TestResult]] = {}
    for r in results:
        categories.setdefault(r.test_id.split("-")[0], []).append(r)

    for cat_name, cat_results in sorted(categories.items()):
        cat_label = {"MUST": "MUST Requirements", "SHOULD": "SHOULD Requirements", "FUNC": "Functional Tests"}.get(
            cat_name, f"{cat_name} Tests"
        )
        lines.append(f"### {cat_label}")
        lines.append("")
        lines.append(f"| ID | Description | Status | Message |")
        lines.append(f"|----|-------------|--------|---------|")
        for r in cat_results:
            icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠️"}.get(r.status, "?")
            msg = r.message.replace("\n", " ") if r.message else ""
            lines.append(f"| {r.test_id} | {r.description} | {icon} {r.status} | {msg} |")
        lines.append("")

    status = "NON-COMPLIANT" if summary["failed"] > 0 else "COMPLIANT"
    lines.append(f"**Overall Status**: {status}")
    return "\n".join(lines)


def _esc(text: str) -> str:
    """Escape XML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _generate_junit(results: list[TestResult], server_url: str) -> str:
    """Generate JUnit XML for GitHub Actions integration."""
    summary = _summarize(results)
    test_cases = []
    failures = []
    for r in results:
        name = _esc(r.test_id) + ": " + _esc(r.description)
        case = '    <testcase classname="oamp_compliance.' + _esc(r.test_id) + '" '
        case += 'name="' + name + '"'
        if r.status == TestResult.FAIL:
            case += ">\n"
            case += '      <failure message="' + _esc(r.message) + '"/>\n'
            case += "    </testcase>"
            failures.append(r)
        elif r.status == TestResult.SKIP:
            case += ">\n"
            case += '      <skipped message="' + _esc(r.message) + '"/>\n'
            case += "    </testcase>"
        else:
            case += " />"
        test_cases.append(case)

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<testsuite name="oamp-compliance" tests="' + str(summary["total"]) + '" '
    xml += 'failures="' + str(summary["failed"]) + '" skipped="' + str(summary["skipped"]) + '">\n'
    xml += "\n".join(test_cases) + "\n"
    if failures:
        xml += "  <system-out>\n"
        for f in failures:
            xml += "    " + _esc(f.test_id) + ": " + _esc(f.message) + "\n"
        xml += "  </system-out>\n"
    xml += "</testsuite>"
    return xml
