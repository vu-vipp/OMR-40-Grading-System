"""Regression tests for stable, unattended OMR camera scanning."""
import cv2
import numpy as np
import pytest

from omr import DEFAULT_KEY, blank_sheet, bubble_xy, code_xy
from live_scan import LiveScanner


def make_sheet():
    im = blank_sheet()
    cv2.circle(im, code_xy(0), 13, (0, 0, 0), -1)
    for q, letter in enumerate(DEFAULT_KEY, 1):
        cv2.circle(im, bubble_xy(q, 'ABCD'.index(letter)), 13, (0, 0, 0), -1)
    return im


class Clock:
    now = 0
    def __call__(self):
        return self.now
    def tick(self, duration=.61):
        self.now += duration


def make_scanner(clock=None, **kwargs):
    return LiveScanner(('101', '102', '103', '104'),
                       {c: DEFAULT_KEY for c in ('101','102','103','104')},
                       clock=clock or Clock(), **kwargs)


def test_auto_grade_after_three_matching_frames():
    clock=Clock(); sc=make_scanner(clock=clock)
    im=make_sheet()
    for n in (1, 2):
        sc.process_frame(im)
        assert sc.snapshot()[1] == n
        assert sc.snapshot()[2] is None
        clock.tick()
    sc.process_frame(im)
    _, count, result = sc.snapshot()
    assert result is not None and count == 3
    assert result.score == 10 and result.correct == 40
    assert result.code == '101'
    assert result.counts['Đúng'] == 40
    assert result.annotated.shape[:2] == (1400, 1000)


def test_same_sheet_not_graded_repeatedly():
    clock=Clock(); sc=make_scanner(clock=clock); im=make_sheet()
    for i in range(8):
        sc.process_frame(im); clock.tick()
    _, count, result = sc.snapshot()
    assert count == 3 and result is not None
    assert sc.snapshot()[2] is result


def test_reset_allows_scan_next_sheet():
    clock=Clock(); sc=make_scanner(clock=clock); im=make_sheet()
    for i in range(3):
        sc.process_frame(im); clock.tick()
    assert sc.snapshot()[2] is not None
    sc.reset()
    assert sc.snapshot()[2] is None
    for i in range(3):
        sc.process_frame(im); clock.tick()
    assert sc.snapshot()[2] is not None


def test_invalid_image_does_not_finalize():
    clock=Clock(); sc=make_scanner(clock=clock)
    im=np.zeros((600,1000,3),dtype=np.uint8)
    for i in range(5):
        sc.process_frame(im); clock.tick()
    message, count, result = sc.snapshot()
    assert result is None and count == 0 and 'Chưa quét được' in message


def test_unreadable_frame_breaks_confirmation():
    clock=Clock(); sc=make_scanner(clock=clock); im=make_sheet()
    sc.process_frame(im); clock.tick()
    assert sc.snapshot()[1] == 1
    sc.process_frame(np.zeros_like(im)); clock.tick()
    assert sc.snapshot()[1] == 0
    sc.process_frame(im); clock.tick()
    assert sc.snapshot()[1] == 1


def test_interval_throttles_frames():
    clock=Clock(); sc=make_scanner(clock=clock,min_interval=2); im=make_sheet()
    sc.process_frame(im); sc.process_frame(im)
    assert sc.snapshot()[1] == 1
    clock.tick(1); sc.process_frame(im)
    assert sc.snapshot()[1] == 1
    clock.tick(1.1); sc.process_frame(im)
    assert sc.snapshot()[1] == 2


def test_unclear_answers_refuse_auto_grade():
    clock=Clock()
    def unclear(_image,_threshold,_margin,codes):
        answers={i:DEFAULT_KEY[i-1] for i in range(1,41)}
        answers[1]='KHONG_RO'
        return '101',answers,{},None,np.full((1400,1000,3),255,np.uint8)
    sc=LiveScanner(('101',),{'101':DEFAULT_KEY},recognize_fn=unclear,clock=clock)
    for i in range(4):
        sc.process_frame(make_sheet()); clock.tick()
    msg,count,result=sc.snapshot()
    assert result is None and count == 0 and 'chưa rõ' in msg


def test_bad_configuration():
    with pytest.raises(ValueError):
        LiveScanner(('101','101'),{'101':DEFAULT_KEY})
    with pytest.raises(ValueError):
        LiveScanner(('101',),{'101':'ABC'})
    with pytest.raises(ValueError):
        LiveScanner(('101',),{'101':DEFAULT_KEY},stable_reads=1)
    with pytest.raises(ValueError):
        LiveScanner(('101',),{'101':DEFAULT_KEY},min_interval=.05)
