"""Tests for repo_probe.builder."""

from repo_probe.builder import render_dockerfile
from repo_probe.detector import TestSetup


def test_pytest_dockerfile_contains_pytest_install() -> None:
    setup = TestSetup("pytest", ["pytest", "-v"], "pyproject.toml", "high")

    content = render_dockerfile(setup)

    assert "FROM python:3.12-slim" in content
    assert "pip install --no-cache-dir 'pytest<9'" in content
    assert 'CMD ["pytest", "-v"]' in content


def test_tox_dockerfile_installs_tox() -> None:
    setup = TestSetup("tox", ["tox"], "tox.ini", "high")

    content = render_dockerfile(setup)

    assert "pip install --no-cache-dir 'tox'" in content
    assert 'CMD ["tox"]' in content


def test_unittest_dockerfile_installs_nothing_extra() -> None:
    setup = TestSetup(
        "unittest",
        ["python", "-m", "unittest", "discover", "-v"],
        ".github/workflows/ci.yml",
        "high",
    )

    content = render_dockerfile(setup)

    assert "pip install --no-cache-dir unittest" not in content
    assert 'CMD ["python", "-m", "unittest", "discover", "-v"]' in content


def test_custom_python_version() -> None:
    setup = TestSetup("pytest", ["pytest", "-v"], "pyproject.toml", "high")

    content = render_dockerfile(setup, python_version="3.11")

    assert "FROM python:3.11-slim" in content