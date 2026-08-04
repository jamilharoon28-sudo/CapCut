"""Automation-first rendering engine (pack docs 15–17).

Coach renders the final MP4 itself with FFmpeg; CapCut is optional. A typed,
versioned RenderGraph is the single source of truth for both preview and final
so approval is meaningful. No paid renderer (Remotion is explicitly excluded).
"""

from .graph import RenderCaption, RenderClip, RenderGraph, RenderStyle
from .renderer import RenderResult, render_graph

__all__ = [
    "RenderCaption",
    "RenderClip",
    "RenderGraph",
    "RenderResult",
    "RenderStyle",
    "render_graph",
]
