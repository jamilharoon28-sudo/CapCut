"""Safety tests S7 (path traversal/symlink) + cloud read-only guard."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from capcut_coach.security import PathSafety, PathSafetyError, is_cloud_path, is_safe_id


def test_path_within_approved_root_ok(tmp_path: Path):
    root = tmp_path / "media"
    root.mkdir()
    f = root / "clip.mov"
    f.write_text("x")
    ps = PathSafety.from_roots([root])
    assert ps.validate(str(f)) == f.resolve()


def test_traversal_escape_is_rejected(tmp_path: Path):
    root = tmp_path / "media"
    root.mkdir()
    (tmp_path / "secret.txt").write_text("s")
    ps = PathSafety.from_roots([root])
    with pytest.raises(PathSafetyError):
        ps.validate(str(root / ".." / "secret.txt"))


def test_symlink_escape_is_rejected(tmp_path: Path):
    root = tmp_path / "media"
    root.mkdir()
    outside = tmp_path / "outside.mov"
    outside.write_text("x")
    link = root / "link.mov"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported here")
    ps = PathSafety.from_roots([root])
    with pytest.raises(PathSafetyError):
        ps.validate(str(link))


def test_shell_metacharacters_rejected(tmp_path: Path):
    root = tmp_path / "media"
    root.mkdir()
    ps = PathSafety.from_roots([root])
    for bad in [str(root) + "; rm -rf /", str(root) + "\n", str(root) + "$(whoami)"]:
        with pytest.raises(PathSafetyError):
            ps.validate(bad, must_exist=False)


def test_cloud_paths_flagged():
    assert is_cloud_path("/Users/x/Library/CloudStorage/GoogleDrive-a/My Drive/clip.mov")
    assert is_cloud_path("/Users/x/Google Drive/raw.mov")
    assert not is_cloud_path("/Users/x/Movies/raw.mov")


def test_safe_id():
    assert is_safe_id("abc-123_XYZ")
    assert not is_safe_id("../etc")
    assert not is_safe_id("a b")
