"""Tests for repo_probe.__main__ (CLI helpers only)."""

from repo_probe.__main__ import _safe_tag


def test_safe_tag_replaces_slash() -> None:
    assert _safe_tag("feature/foo") == "feature-foo"


def test_safe_tag_replaces_colon() -> None:
    assert _safe_tag("v1:rc1") == "v1-rc1"


def test_safe_tag_leaves_plain_ref() -> None:
    assert _safe_tag("8.1.7") == "8.1.7"