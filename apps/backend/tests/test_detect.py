"""P0.1: CapCut bundle detection from a synthetic Info.plist (F1)."""

from __future__ import annotations

import plistlib
from pathlib import Path

from capcut_coach.capcut.detect import read_info_plist_file


def test_reads_version_and_source(tmp_path: Path):
    bundle = tmp_path / "CapCut.app"
    contents = bundle / "Contents"
    contents.mkdir(parents=True)
    info = contents / "Info.plist"
    with open(info, "wb") as f:
        plistlib.dump(
            {
                "CFBundleShortVersionString": "3.1.0",
                "CFBundleVersion": "4200",
                "appSource": "cc",
            },
            f,
        )
    result = read_info_plist_file(info)
    assert result.found
    assert result.short_version == "3.1.0"
    assert result.build == "4200"
    assert result.is_international is True
