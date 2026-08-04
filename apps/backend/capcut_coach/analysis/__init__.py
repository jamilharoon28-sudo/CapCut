"""Local footage understanding (pack doc 15 §6): pick the best moment in each
clip and reframe on the subject. Deterministic + cv2-optional; no network, no
paid services, no model downloads (Haar cascades ship with OpenCV).
"""

from .visual import ClipAnalysis, analyse_clip, cv2_available

__all__ = ["ClipAnalysis", "analyse_clip", "cv2_available"]
