"""Rights-gated Approved Music library (pack doc 20 §3).

Coach may automatically choose music ONLY from owner-approved local folders (or a
read-only Drive folder staged locally). It NEVER rips, records, downloads or
extracts music from streaming services, reference videos, or arbitrary websites —
there is no network or download code path in this package by design.
"""

from .library import index_music
from .schemas import MusicAsset, MusicSelection, RightsStatus
from .select import select_music

__all__ = ["MusicAsset", "MusicSelection", "RightsStatus", "index_music", "select_music"]
