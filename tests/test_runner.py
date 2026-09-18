"""Tests for repo_probe.runner."""

from repo_probe.runner import TestRun


def test_passed_true_when_exit_code_zero() -> None:
    run = TestRun(exit_code=0, stdout="ok", stderr="", duration_seconds=1.0)
    assert run.passed is True


def test_passed_false_when_exit_code_nonzero() -> None:
    run = TestRun(exit_code=1, stdout="", stderr="fail", duration_seconds=1.0)
    assert run.passed is False


def test_testrun_is_immutable() -> None:
    run = TestRun(exit_code=0, stdout="", stderr="", duration_seconds=0.5)
    try:
        run.exit_code = 1  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("TestRun should be immutable")