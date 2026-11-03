"""Camera-photo regression tests: ink inside real printed circles vs warped fixed coordinates.

Do not include or publish real student/user photos in this repository.
Synthetic curves simulate the residual bending seen on A4 webcam sheets.
"""
import cv2
import numpy as np
import pytest

from omr import CODES, DEFAULT_KEY, SheetError, blank_sheet, bubble_xy, code_xy
from omr import _calibrate_bubble_centers, grade, recognize


def curved_photo(with_code=True, two_codes=False):
    image = blank_sheet(CODES)
    if with_code:
        cv2.circle(image, code_xy(0), 13, (0, 0, 0), -1)
    if two_codes:
        cv2.circle(image, code_xy(1), 13, (0, 0, 0), -1)
    for q, answer in enumerate(DEFAULT_KEY, 1):
        cv2.circle(image, bubble_xy(q, 'ABCD'.index(answer)), 13, (0, 0, 0), -1)

    height, width = image.shape[:2]
    xx, yy = np.meshgrid(
        np.arange(width, dtype=np.float32),
        np.arange(height, dtype=np.float32),
    )
    # A gently curved sheet: at middle rows actual bubble centers move
    # by up to 22px, while the four black corner markers remain in place.
    shift = 22 * np.sin(np.pi * (yy - 65) / 1270)**2 * (.6 + .4 * xx / width)
    return cv2.remap(image, xx - shift, yy, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT,
                     borderValue=(255, 255, 255))


def test_curved_camera_photo_uses_actual_circle_centers():
    image = curved_photo()
    code, answers, _, _, aligned = recognize(image, codes=CODES)
    assert code == '101'
    assert ''.join(answers[q] for q in range(1, 41)) == DEFAULT_KEY
    assert grade(answers, DEFAULT_KEY)[1] == 10.0
    calibrated = _calibrate_bubble_centers(aligned)
    assert calibrated is not None
    assert len(calibrated) == 164


@pytest.mark.parametrize('without_code,two_codes', [(True, False), (False, True)])
def test_curved_photo_still_refuses_invalid_exam_code(without_code, two_codes):
    image = curved_photo(with_code=not without_code, two_codes=two_codes)
    with pytest.raises(SheetError):
        recognize(image, codes=CODES)


def test_normal_printed_sheet_remains_readable():
    img = blank_sheet(CODES)
    cv2.circle(img, code_xy(2), 13, (0, 0, 0), -1)
    for q, answer in enumerate(DEFAULT_KEY, 1):
        cv2.circle(img, bubble_xy(q, 'ABCD'.index(answer)), 13, (0, 0, 0), -1)
    code, answers, *_ = recognize(img, codes=CODES)
    assert code == '103'
    assert grade(answers, DEFAULT_KEY)[1] == 10.0
