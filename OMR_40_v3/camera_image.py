"""Simple camera orientation controls.

Correct the *raw* captured image before feeding it to OMR. This is different
from a cosmetic CSS mirror: an inverted image needs consistent correction for
both recognition and preview.
"""
from __future__ import annotations

import cv2
import numpy as np

CAMERA_ORIENTATIONS = (
    'Giữ nguyên',
    'Lật ngang (đảo gương)',
    'Lật dọc',
    'Xoay 180°',
)


def orient_frame(image: np.ndarray, mode: str) -> np.ndarray:
    """Return the reoriented image without mutating original pixels."""
    if mode == CAMERA_ORIENTATIONS[0]:
        return image
    if mode == CAMERA_ORIENTATIONS[1]:
        return cv2.flip(image, 1)
    if mode == CAMERA_ORIENTATIONS[2]:
        return cv2.flip(image, 0)
    if mode == CAMERA_ORIENTATIONS[3]:
        return cv2.rotate(image, cv2.ROTATE_180)
    raise ValueError('Chế độ lật camera không hợp lệ.')


def sharpen_preview(image: np.ndarray, enabled: bool) -> np.ndarray:
    """Slight cosmetic sharpening for displayed frames ONLY, never OMR input.

    This cannot restore information lost due to defocus, motion blur, or a
    camera that has negotiated a low resolution.
    """
    if not enabled:
        return image
    blurred = cv2.GaussianBlur(image, (0, 0), 1.1)
    return cv2.addWeighted(image, 1.35, blurred, -0.35, 0)
