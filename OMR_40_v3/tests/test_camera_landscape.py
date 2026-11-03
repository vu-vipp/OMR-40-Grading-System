"""Regression: a portrait A4 OMR page must be found in a 16:9 webcam frame."""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from omr import CODES, DEFAULT_KEY, SheetError, blank_sheet, bubble_xy, code_xy, grade, recognize


def marked_sheet():
    sheet = blank_sheet(CODES)
    cv2.circle(sheet, code_xy(0), 13, (0, 0, 0), -1)
    for q, letter in enumerate(DEFAULT_KEY, start=1):
        cv2.circle(sheet, bubble_xy(q, 'ABCD'.index(letter)), 13, (0, 0, 0), -1)
    return sheet


@pytest.mark.parametrize('scale', [.60, .70])
def test_centered_portrait_sheet_inside_landscape_webcam(scale):
    sheet = marked_sheet()
    width, height = int(1000 * scale), int(1400 * scale)
    photo = np.full((1080, 1920, 3), 255, np.uint8)
    scaled = cv2.resize(sheet, (width, height), interpolation=cv2.INTER_AREA)
    x, y = (1920 - width) // 2, (1080 - height) // 2
    photo[y:y+height, x:x+width] = scaled

    # Old _find_markers() rejected this because marker positions were not
    # inside the outer 28% corner zones of the 16:9 camera frame.
    code, answers, *_ = recognize(photo, codes=CODES)
    assert code == '101'
    assert grade(answers, DEFAULT_KEY)[1] == 10


def test_centred_sheet_with_perspective_in_landscape_webcam():
    sheet = marked_sheet()
    src = np.float32([[0,0], [999,0], [999,1399], [0,1399]])
    dest = np.float32([[660,100], [1260,70], [1250,990], [630,1010]])
    transform = cv2.getPerspectiveTransform(src, dest)
    photo = cv2.warpPerspective(
        sheet, transform, (1920, 1080),
        borderValue=(255,255,255),
    )
    code, answers, *_ = recognize(photo, codes=CODES)
    assert code == '101'
    assert grade(answers, DEFAULT_KEY)[1] == 10


def test_reject_plain_landscape_background():
    photo = np.full((1080, 1920, 3), 255, np.uint8)
    with pytest.raises(SheetError):
        recognize(photo, codes=CODES)
