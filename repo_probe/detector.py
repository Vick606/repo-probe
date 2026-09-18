"""Detect how to run tests for a cloned Python repository."""

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestSetup:
    """Result of detecting how a repo runs its tests."""

    __test__ = False  # tell pytest not to collect this class

    runner: str                    # runner the harness will use
    command: list[str]             # command to execute
    source: str                    # file that informed the decision
    confidence: str                # "high" | "medium" | "low"
    ci_runner: str | None = None   # runner the repo's CI uses, if any


_RUNNER_COMMANDS: dict[str, list[str]] = {
    "pytest": ["pytest", "-v"],
    "unittest": ["python", "-m", "unittest", "discover", "-v"],
    "tox": ["tox"],
    "nox": ["nox"],
}


def _scan_workflows(repo_path: Path) -> tuple[str | None, str | None]:
    """Inspect .github/workflows/*.yml for the runner the CI uses.

    Returns (runner, source_file) or (None, None) if nothing is found.
    """
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return None, None

    for wf in sorted(workflows_dir.iterdir()):
        if wf.suffix not in {".yml", ".yaml"}:
            continue
        try:
            content = wf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        source = f".github/workflows/{wf.name}"
        if "tox" in content:
            return "tox", source
        if "nox" in content:
            return "nox", source
        if "pytest" in content:
            return "pytest", source
        if "unittest" in content:
            return "unittest", source
    return None, None


def _find_pytest_source(repo_path: Path) -> str | None:
    """Return a file (or dir) that signals pytest config, or None."""
    if (repo_path / "pytest.ini").is_file():
        return "pytest.ini"

    pyproject = repo_path / "pyproject.toml"
    if pyproject.is_file():
        try:
            if "pytest" in pyproject.read_text(encoding="utf-8", errors="ignore"):
                return "pyproject.toml"
        except OSError:
            pass

    setup_cfg = repo_path / "setup.cfg"
    if setup_cfg.is_file():
        try:
            if "pytest" in setup_cfg.read_text(encoding="utf-8", errors="ignore"):
                return "setup.cfg"
        except OSError:
            pass

    if (repo_path / "conftest.py").is_file():
        return "conftest.py"

    tests_dir = repo_path / "tests"
    if tests_dir.is_dir() and any(tests_dir.glob("test_*.py")):
        return "tests/"

    return None


def detect_test_setup(repo_path: Path) -> TestSetup:
    """Return the best-guess test setup for a cloned Python repo.

    Strategy:
      1. If a pytest config exists anywhere, use pytest. Record CI runner.
      2. Else if a CI workflow names a runner, use it.
      3. Else if tox.ini exists, use tox.
      4. Else if noxfile.py exists, use nox.
      5. Fallback: pytest -v with low confidence.
    """
    repo_path = Path(repo_path)
    ci_runner, ci_source = _scan_workflows(repo_path)

    pytest_source = _find_pytest_source(repo_path)
    if pytest_source is not None:
        return TestSetup(
            runner="pytest",
            command=_RUNNER_COMMANDS["pytest"],
            source=pytest_source,
            confidence="high",
            ci_runner=ci_runner,
        )

    if ci_runner is not None:
        return TestSetup(
            runner=ci_runner,
            command=_RUNNER_COMMANDS[ci_runner],
            source=ci_source or ".github/workflows",
            confidence="high",
            ci_runner=ci_runner,
        )

    if (repo_path / "tox.ini").is_file():
        return TestSetup("tox", _RUNNER_COMMANDS["tox"], "tox.ini", "high")

    if (repo_path / "noxfile.py").is_file():
        return TestSetup("nox", _RUNNER_COMMANDS["nox"], "noxfile.py", "high")

    return TestSetup(
        runner="pytest",
        command=_RUNNER_COMMANDS["pytest"],
        source="fallback",
        confidence="low",
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m repo_probe.detector <repo_path>")
        sys.exit(1)

    setup = detect_test_setup(Path(sys.argv[1]))
    print(f"runner:     {setup.runner}")
    print(f"command:    {' '.join(setup.command)}")
    print(f"source:     {setup.source}")
    print(f"confidence: {setup.confidence}")
    print(f"ci_runner:  {setup.ci_runner or '-'}")