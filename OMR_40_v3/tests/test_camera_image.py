"""Orientation controls affect real OMR input, not just mirrored CSS preview."""
import cv2
import numpy as np
import pytest

from camera_image import CAMERA_ORIENTATIONS, orient_frame, sharpen_preview
from omr import DEFAULT_KEY, CODES, blank_sheet, bubble_xy, code_xy, recognize


@pytest.mark.parametrize('orientation,expected', [
    ('Giữ nguyên', lambda x:x),
    ('Lật ngang (đảo gương)', lambda x:cv2.flip(x, 1)),
    ('Lật dọc', lambda x:cv2.flip(x, 0)),
    ('Xoay 180°', lambda x:cv2.rotate(x, cv2.ROTATE_180)),
])
def test_camera_orientation_matches_opencv(orientation, expected):
    img=np.arange(3*7*3,dtype=np.uint8).reshape(3,7,3)
    original=img.copy()
    result=orient_frame(img,orientation)
    assert np.array_equal(result,expected(original))
    assert np.array_equal(img,original)


@pytest.mark.parametrize('orientation', CAMERA_ORIENTATIONS)
def test_sheet_is_readable_after_camera_correction(orientation):
    img=blank_sheet()
    cv2.circle(img, code_xy(0),13,(0,0,0),-1)
    for q,answer in enumerate(DEFAULT_KEY,1):
        cv2.circle(img,bubble_xy(q,'ABCD'.index(answer)),13,(0,0,0),-1)
    # Camera sends an image in the opposite orientation (all modes involutive).
    inverted=orient_frame(img,orientation)
    corrected=orient_frame(inverted,orientation)
    code,answers,*_=recognize(corrected,codes=CODES)
    assert code=='101'
    assert ''.join(answers[q] for q in range(1,41))==DEFAULT_KEY


def test_invalid_orientation_is_rejected():
    with pytest.raises(ValueError):
        orient_frame(np.zeros((3,3,3),dtype=np.uint8),'45 degree')


def test_preview_sharpen_only_changes_copy():
    image=np.zeros((80,100,3),dtype=np.uint8)
    image[20:60,30:80]=175
    original=image.copy()
    preview=sharpen_preview(image.copy(),True)
    assert preview.shape==image.shape
    assert np.array_equal(image,original)
    assert not np.array_equal(preview,original)
    assert sharpen_preview(image,False) is image


def test_camera_options_are_wired_into_webrtc():
    from pathlib import Path
    code=(Path(__file__).parents[1]/'live_camera_ui.py').read_text(encoding='utf-8')
    assert "'facingMode': {'ideal': facing}" in code
    assert "quality.startswith('Full HD')" in code
    assert 'scanner.process_frame(image)' in code
    assert 'image = orient_frame(camera_image, orientation)' in code
    assert 'sharpen_preview(image.copy(), sharpen)' in code
    assert 'VIDEO:' in code
