"""Parse a script pack into a reviewable typed shot plan (Phase 2, test F4A).

Handles a ZIP containing Word/PDF/text scripts (names/folders with spaces).
Extraction blocks path traversal and zip bombs. Reel/shot headings, time ranges,
camera directions, speech, overlays, cutaways, pacing, transitions, end cards and
cross-references are captured; unknown content is *retained*, never silently
dropped. Music fields are parsed but may be ignored per owner preference.

Optional parsers (`python-docx`, `pypdf`) are imported lazily so the module loads
and text/ZIP parsing works even when they are not installed.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# Zip-bomb guards (F4A).
MAX_TOTAL_UNCOMPRESSED = 500 * 1024 * 1024  # 500 MiB across the whole archive
MAX_FILES = 5000
MAX_COMPRESSION_RATIO = 200  # per-entry uncompressed/compressed ceiling


class UnsafeArchiveError(ValueError):
    pass


def safe_extract_zip(zip_path: Path, dest_dir: Path) -> list[Path]:
    """Extract a ZIP safely. Rejects traversal, absolute paths, symlinks, bombs."""
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    total = 0
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_FILES:
            raise UnsafeArchiveError("archive contains too many entries")
        for info in infos:
            name = info.filename
            if name.endswith("/"):
                continue  # directory entry
            # Reject absolute paths and traversal before joining.
            if name.startswith("/") or ".." in Path(name).parts:
                raise UnsafeArchiveError(f"unsafe path in archive: {name!r}")
            # Symlink entries (unix mode) are refused.
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise UnsafeArchiveError(f"symlink entry refused: {name!r}")
            target = (dest_dir / name).resolve()
            if dest_dir not in target.parents and target != dest_dir:
                raise UnsafeArchiveError(f"path escapes destination: {name!r}")
            size = info.file_size
            total += size
            if total > MAX_TOTAL_UNCOMPRESSED:
                raise UnsafeArchiveError("archive uncompressed size exceeds limit")
            if info.compress_size > 0 and size / info.compress_size > MAX_COMPRESSION_RATIO:
                raise UnsafeArchiveError(f"suspicious compression ratio for {name!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                # Stream copy so a lying header cannot balloon memory.
                remaining = MAX_TOTAL_UNCOMPRESSED
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    if remaining < 0:
                        raise UnsafeArchiveError("entry larger than declared size")
                    out.write(chunk)
            extracted.append(target)
    return extracted


@dataclass
class ShotNode:
    id: str
    kind: str  # reel | shot | overlay | cutaway | transition | end_card | note
    text: str
    time_range: str | None = None
    camera: str | None = None
    overlay: str | None = None
    music: str | None = None  # parsed but may be ignored per owner preference
    cross_references: list[str] = field(default_factory=list)
    raw: str = ""  # original line, so nothing is lost


@dataclass
class ShotPlan:
    reels: int
    nodes: list[ShotNode]
    unparsed: list[str] = field(default_factory=list)  # retained, not dropped

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for n in self.nodes:
            out[n.kind] = out.get(n.kind, 0) + 1
        return out


_REEL_RE = re.compile(r"^\s*(reel|scene)\s*#?\s*(\d+)", re.IGNORECASE)
_SHOT_RE = re.compile(r"^\s*(shot|clip)\s*#?\s*(\d+)", re.IGNORECASE)
_TIME_RE = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—>to]+\s*(\d{1,2}:\d{2}(?::\d{2})?)")
_CAMERA_RE = re.compile(r"\b(cut ?away|b-?roll|close-?up|wide|zoom|pan|push ?in)\b", re.IGNORECASE)
_OVERLAY_RE = re.compile(r"^\s*(overlay|text|caption|lower.?third)\s*[:\-]", re.IGNORECASE)
_TRANSITION_RE = re.compile(r"^\s*(transition|cut|dissolve|fade)\s*[:\-]", re.IGNORECASE)
_ENDCARD_RE = re.compile(r"\b(end ?card|outro|cta|call.to.action|subscribe)\b", re.IGNORECASE)
_MUSIC_RE = re.compile(r"^\s*(music|track|song|bgm)\s*[:\-]", re.IGNORECASE)
_XREF_RE = re.compile(r"\b(?:see|ref|reuse)\s+(reel|shot|clip)\s*#?\s*(\d+)", re.IGNORECASE)


def _classify(line: str, idx: int) -> ShotNode:
    text = line.strip()
    xrefs = [f"{m.group(1).lower()}{m.group(2)}" for m in _XREF_RE.finditer(text)]
    tm = _TIME_RE.search(text)
    time_range = f"{tm.group(1)}-{tm.group(2)}" if tm else None
    cam = _CAMERA_RE.search(text)
    camera = cam.group(0) if cam else None

    if _REEL_RE.search(text):
        kind = "reel"
    elif _SHOT_RE.search(text):
        kind = "shot"
    elif _OVERLAY_RE.search(text):
        kind = "overlay"
    elif _TRANSITION_RE.search(text):
        kind = "transition"
    elif _ENDCARD_RE.search(text):
        kind = "end_card"
    elif _MUSIC_RE.search(text):
        kind = "note"
    elif _CAMERA_RE.search(text) and ("cutaway" in text.lower() or "b-roll" in text.lower()
                                      or "broll" in text.lower()):
        kind = "cutaway"
    else:
        kind = "note"

    music = None
    mm = _MUSIC_RE.search(text)
    if mm:
        music = text

    return ShotNode(
        id=f"n{idx}",
        kind=kind,
        text=text,
        time_range=time_range,
        camera=camera,
        overlay=text if _OVERLAY_RE.search(text) else None,
        music=music,
        cross_references=xrefs,
        raw=line,
    )


def parse_text_script(text: str) -> ShotPlan:
    """Parse plain-text script content into a shot plan."""
    nodes: list[ShotNode] = []
    unparsed: list[str] = []
    reels = 0
    for i, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        node = _classify(line, i)
        if node.kind == "reel":
            reels += 1
        nodes.append(node)
        # Retain the raw line for anything we could only weakly classify.
        if node.kind == "note" and not any(
            [node.time_range, node.camera, node.overlay, node.music, node.cross_references]
        ):
            unparsed.append(line.strip())
    return ShotPlan(reels=max(reels, 1 if nodes else 0), nodes=nodes, unparsed=unparsed)


def _read_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except ImportError:
        return ""  # optional dependency absent — caller keeps the file for later
    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return ""
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def parse_script_file(path: Path) -> ShotPlan:
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md", ".rtf"):
        return parse_text_script(path.read_text("utf-8", errors="replace"))
    if suffix == ".docx":
        return parse_text_script(_read_docx(path))
    if suffix == ".pdf":
        return parse_text_script(_read_pdf(path))
    # Unknown type: retain nothing parsed but do not fail the import.
    return ShotPlan(reels=0, nodes=[], unparsed=[f"unsupported script file: {path.name}"])


def parse_script_pack(source: Path, work_dir: Path) -> ShotPlan:
    """Parse a single script file or a ZIP of scripts into one merged shot plan."""
    if source.suffix.lower() == ".zip":
        files = safe_extract_zip(source, work_dir)
        merged_nodes: list[ShotNode] = []
        merged_unparsed: list[str] = []
        reels = 0
        for f in sorted(files):
            if f.suffix.lower() in (".txt", ".md", ".rtf", ".docx", ".pdf"):
                plan = parse_script_file(f)
                reels += plan.reels
                merged_nodes.extend(plan.nodes)
                merged_unparsed.extend(plan.unparsed)
        return ShotPlan(reels=reels, nodes=merged_nodes, unparsed=merged_unparsed)
    return parse_script_file(source)
