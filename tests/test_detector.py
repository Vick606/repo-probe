"""Tests for repo_probe.detector."""

from pathlib import Path

from repo_probe.detector import detect_test_setup


def test_pytest_config_wins_over_tox_ci(tmp_path: Path) -> None:
    """A repo whose CI uses tox but has pytest config should use pytest."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "tests.yaml").write_text("steps:\n  - run: tox\n")
    (tmp_path / "setup.cfg").write_text("[tool:pytest]\ntestpaths = tests\n")

    setup = detect_test_setup(tmp_path)

    assert setup.runner == "pytest"
    assert setup.source == "setup.cfg"
    assert setup.confidence == "high"
    assert setup.ci_runner == "tox"


def test_workflow_only_repo_uses_ci_runner(tmp_path: Path) -> None:
    """No pytest config: fall back to the runner the CI names."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "ci.yml").write_text("steps:\n  - run: pytest -v\n")

    setup = detect_test_setup(tmp_path)

    assert setup.runner == "pytest"
    assert setup.confidence == "high"
    assert setup.ci_runner == "pytest"
    assert "ci.yml" in setup.source


def test_detects_tox_from_tox_ini(tmp_path: Path) -> None:
    (tmp_path / "tox.ini").write_text("[tox]\nenvlist = py312\n")

    setup = detect_test_setup(tmp_path)

    assert setup.runner == "tox"
    assert setup.source == "tox.ini"
    assert setup.confidence == "high"
    assert setup.ci_runner is None


def test_pytest_ini_takes_precedence(tmp_path: Path) -> None:
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "setup.cfg").write_text("[tool:pytest]\n")

    setup = detect_test_setup(tmp_path)

    assert setup.runner == "pytest"
    assert setup.source == "pytest.ini"


def test_fallback_when_no_signals(tmp_path: Path) -> None:
    setup = detect_test_setup(tmp_path)

    assert setup.runner == "pytest"
    assert setup.source == "fallback"
    assert setup.confidence == "low"
    assert setup.ci_runner is None