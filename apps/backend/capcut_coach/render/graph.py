"""Typed RenderGraph — source of truth for preview and final (pack doc 15 §3).

Times are integer microseconds. A graph carries enough to compile a
deterministic FFmpeg command: clips with source in/out and timeline placement,
per-clip reframe/speed/colour, captions, and overlays. Provenance links every
node back to the decision and source that produced it (doc 17 §8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..schemas.edit_plan import Canvas, EditPlan


@dataclass
class RenderStyle:
    """Variant look (Clean / Enhanced / Bold) applied uniformly to a graph."""

    name: str = "clean"
    captions: bool = False
    # eq filter params (contrast/brightness/saturation) — 1.0 = neutral.
    contrast: float = 1.0
    brightness: float = 0.0
    saturation: float = 1.0
    loudnorm: bool = True          # normalise dialogue loudness
    ken_burns: bool = False        # gentle push-in for life on static shots
    caption_fill: str = "&H00FFFFFF"   # ASS colour (white)
    caption_outline: str = "&H00000000"  # black outline
    accent: str = "#6D5DFB"


# Ken Burns is kept as an off-by-default option; the zoompan path needs more
# tuning before it is reliable/fast enough to ship on by default.
CLEAN = RenderStyle(name="clean", captions=False, loudnorm=True, ken_burns=False)
ENHANCED = RenderStyle(
    name="enhanced", captions=True, contrast=1.06, saturation=1.08, loudnorm=True,
    ken_burns=False,
)
BOLD = RenderStyle(
    name="bold", captions=True, contrast=1.12, saturation=1.18, brightness=0.02,
    loudnorm=True, ken_burns=False, caption_fill="&H0000E1FF",  # amber emphasis
)

STYLES = {"clean": CLEAN, "enhanced": ENHANCED, "bold": BOLD}


@dataclass
class RenderClip:
    asset_path: Path
    source_start_us: int
    source_duration_us: int
    timeline_start_us: int
    has_audio: bool = True
    role: str = "point"
    crop_x_norm: float = 0.0   # subject reframe: -1 left .. 0 centre .. +1 right
    ken_burns: bool = False    # gentle push-in for life on static shots
    provenance: dict = field(default_factory=dict)

    @property
    def source_start_s(self) -> float:
        return self.source_start_us / 1_000_000

    @property
    def duration_s(self) -> float:
        return self.source_duration_us / 1_000_000


@dataclass
class RenderCaption:
    text: str
    start_us: int
    duration_us: int


@dataclass
class Outro:
    """A branded ending (pack doc 18): a logo over a solid background."""

    logo_path: Path | None
    duration_us: int = 4_500_000
    bg_color: str = "0x111318"


@dataclass
class RenderGraph:
    schema_version: int
    canvas: Canvas
    clips: list[RenderClip]
    captions: list[RenderCaption] = field(default_factory=list)
    style: RenderStyle = field(default_factory=lambda: CLEAN)
    project_id: str = ""
    edit_plan_id: str = ""
    music_path: Path | None = None   # music bed; replaces clip audio for montages
    outro: Outro | None = None

    @property
    def clips_total_us(self) -> int:
        return sum(c.source_duration_us for c in self.clips)

    @property
    def total_us(self) -> int:
        extra = self.outro.duration_us if self.outro else 0
        return self.clips_total_us + extra


def graph_from_edit_plan(
    plan: EditPlan,
    asset_paths: dict[str, Path],
    *,
    style: RenderStyle,
    asset_has_audio: dict[str, bool] | None = None,
) -> RenderGraph:
    """Compile an EditPlan (+ media catalog) into a renderable graph."""
    asset_has_audio = asset_has_audio or {}
    clips: list[RenderClip] = []
    for seg in sorted(plan.segments, key=lambda s: s.timeline_start_us):
        path = asset_paths.get(seg.asset_id)
        if path is None:
            continue
        clips.append(
            RenderClip(
                asset_path=path,
                source_start_us=seg.source_start_us,
                source_duration_us=seg.source_duration_us,
                timeline_start_us=seg.timeline_start_us,
                has_audio=asset_has_audio.get(seg.asset_id, True),
                role=seg.role,
                crop_x_norm=float(seg.transform.x),   # reframe offset carried in transform.x
                ken_burns=style.ken_burns,
                provenance={"segment_id": seg.id, "reason": seg.reason,
                            "confidence": seg.confidence},
            )
        )
    captions = [
        RenderCaption(text=c.text, start_us=c.start_us, duration_us=c.duration_us)
        for c in plan.captions
    ] if style.captions else []
    return RenderGraph(
        schema_version=1,
        canvas=plan.canvas,
        clips=clips,
        captions=captions,
        style=style,
        project_id=plan.project_id,
        edit_plan_id=plan.id,
    )
