"""Tests for repo_probe.cloner."""

from pathlib import Path

import pytest

from repo_probe.cloner import clone_repo


HELLO_WORLD = "https://github.com/octocat/Hello-World.git"


def test_clone_creates_repo(tmp_path: Path) -> None:
    """Clone succeeds into an empty destination and creates a working repo."""
    dest = tmp_path / "hello"
    clone_repo(HELLO_WORLD, "HEAD", dest)

    # A real git repo has a .git directory.
    assert (dest / ".git").is_dir()
    # And it contains at least one file.
    assert any(dest.iterdir())


def test_clone_rejects_nonempty_dest(tmp_path: Path) -> None:
    """Clone refuses to overwrite a non-empty destination."""
    dest = tmp_path / "hello"
    dest.mkdir()
    (dest / "existing.txt").write_text("nope")

    with pytest.raises(FileExistsError):
        clone_repo(HELLO_WORLD, "HEAD", dest)