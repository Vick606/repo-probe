"""Write a structured JSON evaluation report."""

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from repo_probe.detector import TestSetup
from repo_probe.runner import TestRun


SCHEMA_VERSION = "1.0"
STDOUT_TAIL_LINES = 50
STDERR_TAIL_LINES = 20


def _tail(text: str, max_lines: int) -> str:
    """Return the last N lines of text, joined back with newlines."""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def build_report(
    repo_url: str,
    ref: str,
    commit: str,
    setup: TestSetup,
    run: TestRun,
) -> dict:
    """Build a serializable evaluation report as a dict."""
    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": {
            "url": repo_url,
            "ref": ref,
            "commit": commit,
        },
        "setup": asdict(setup),
        "result": {
            "exit_code": run.exit_code,
            "passed": run.passed,
            "duration_seconds": round(run.duration_seconds, 2),
            "stdout_tail": _tail(run.stdout, STDOUT_TAIL_LINES),
            "stderr_tail": _tail(run.stderr, STDERR_TAIL_LINES),
        },
    }


def write_report(report: dict, output_path: Path) -> Path:
    """Write the report to disk as JSON. Returns the path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m repo_probe.reporter <report.json>")
        print("(Prints the example schema to stdout; does not run anything.)")
        sys.exit(1)

    example = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": {"url": "...", "ref": "...", "commit": "..."},
        "setup": {
            "runner": "pytest",
            "command": ["pytest", "-v"],
            "source": "setup.cfg",
            "confidence": "high",
            "ci_runner": "tox",
        },
        "result": {
            "exit_code": 0,
            "passed": True,
            "duration_seconds": 1.92,
            "stdout_tail": "...",
            "stderr_tail": "",
        },
    }
    write_report(example, Path(sys.argv[1]))
    print(f"wrote example report to {sys.argv[1]}")