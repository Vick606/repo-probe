"""Tests for repo_probe.reporter."""

import json
from pathlib import Path

from repo_probe.detector import TestSetup
from repo_probe.reporter import (
    SCHEMA_VERSION,
    _tail,
    build_report,
    write_report,
)
from repo_probe.runner import TestRun


def _sample_setup() -> TestSetup:
    return TestSetup("pytest", ["pytest", "-v"], "setup.cfg", "high", ci_runner="tox")


def _sample_run() -> TestRun:
    return TestRun(
        exit_code=0,
        stdout="a\nb\nc\n",
        stderr="",
        duration_seconds=1.234,
    )


def test_build_report_has_expected_structure() -> None:
    report = build_report(
        repo_url="https://example.com/repo.git",
        ref="v1.0",
        commit="abc123",
        setup=_sample_setup(),
        run=_sample_run(),
    )

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["repo"] == {
        "url": "https://example.com/repo.git",
        "ref": "v1.0",
        "commit": "abc123",
    }
    assert report["setup"]["runner"] == "pytest"
    assert report["setup"]["ci_runner"] == "tox"
    assert report["result"]["passed"] is True
    assert report["result"]["duration_seconds"] == 1.23
    assert "timestamp" in report


def test_build_report_serializes_to_json() -> None:
    report = build_report(
        repo_url="u",
        ref="r",
        commit="c",
        setup=_sample_setup(),
        run=_sample_run(),
    )

    # Should not raise.
    text = json.dumps(report)
    assert SCHEMA_VERSION in text


def test_tail_short_text_unchanged() -> None:
    assert _tail("a\nb\nc", 10) == "a\nb\nc"


def test_tail_truncates_to_last_n_lines() -> None:
    text = "\n".join(str(i) for i in range(100))
    result = _tail(text, 5)
    assert result == "\n".join(str(i) for i in range(95, 100))


def test_write_report_creates_file(tmp_path: Path) -> None:
    report = build_report(
        repo_url="u",
        ref="r",
        commit="c",
        setup=_sample_setup(),
        run=_sample_run(),
    )
    out = tmp_path / "nested" / "report.json"

    written = write_report(report, out)

    assert written == out
    assert out.is_file()
    loaded = json.loads(out.read_text())
    assert loaded["schema_version"] == SCHEMA_VERSION