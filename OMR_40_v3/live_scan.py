"""Thread-safe state machine for live OMR scanning over camera video frames.

OpenCV and the reader run in a WebRTC worker, without Streamlit API calls.
A result is accepted only after consecutive matching, unambiguous reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Callable

import cv2
import numpy as np

from omr import annotate_grading, grade, normalize_key, recognize, summary


@dataclass(frozen=True)
class LiveResult:
    code: str
    score: float
    correct: int
    rows: tuple[dict, ...]
    counts: dict[str, int]
    frame: np.ndarray
    annotated: np.ndarray


class LiveScanner:
    """Accept a sheet after N consecutive identical, confident OMR scans.

    A successful result stays frozen until reset() is called. This prevents
    accidental duplicate grading when the user keeps holding the same page.
    """

    def __init__(self, codes, keys, threshold=.24, margin=.055,
                 stable_reads=3, min_interval=.6,
                 recognize_fn: Callable = recognize,
                 clock: Callable[[], float] = monotonic):
        self.codes = tuple(codes)
        self.keys = {code: normalize_key(keys[code]) for code in self.codes}
        if not 1 <= len(self.codes) <= 4 or len(set(self.codes)) != len(self.codes):
            raise ValueError('Nhóm mã đề không hợp lệ.')
        if not 2 <= stable_reads <= 10:
            raise ValueError('Cần từ 2 đến 10 lần đọc trùng nhau.')
        if not .1 <= min_interval <= 5:
            raise ValueError('Khoảng cách quét không hợp lệ.')
        self.threshold = threshold
        self.margin = margin
        self.stable_reads = stable_reads
        self.min_interval = min_interval
        self._recognize = recognize_fn
        self._clock = clock
        self._state_lock = Lock()
        self._work_lock = Lock()
        self._last_attempt = float('-inf')
        self._signature = None
        self._streak = 0
        self._status = 'Đang tìm phiếu trong khung hình…'
        self._result: LiveResult | None = None

    def reset(self) -> None:
        with self._state_lock:
            self._signature = None
            self._streak = 0
            self._status = 'Sẵn sàng quét phiếu tiếp theo.'
            self._result = None
            self._last_attempt = float('-inf')

    def snapshot(self) -> tuple[str, int, LiveResult | None]:
        with self._state_lock:
            return self._status, self._streak, self._result

    def process_frame(self, image: np.ndarray) -> None:
        # WebRTC can provide frames from multiple threads. Drop overlapping work.
        if not self._work_lock.acquire(blocking=False):
            return
        try:
            with self._state_lock:
                if self._result is not None:
                    return
                now = self._clock()
                if now - self._last_attempt < self.min_interval:
                    return
                self._last_attempt = now
            try:
                code, answers, _ratios, _marked, aligned = self._recognize(
                    image, self.threshold, self.margin, codes=self.codes,
                )
                if code not in self.keys:
                    raise ValueError('Chưa có đáp án chuẩn cho mã đề nhận diện.')
                rows, score, correct, pending = grade(answers, self.keys[code])
                if pending:
                    with self._state_lock:
                        self._signature = None
                        self._streak = 0
                        self._status = f'Có {pending} câu chưa rõ; giữ phiếu ổn định và tăng ánh sáng.'
                    return
                signature = (code, tuple(answers[q] for q in range(1, 41)))
                with self._state_lock:
                    if self._signature == signature:
                        self._streak += 1
                    else:
                        self._signature = signature
                        self._streak = 1
                    streak = self._streak
                    self._status = f'Đã đọc mã {code}, đang xác nhận {streak}/{self.stable_reads}…'
                if streak >= self.stable_reads:
                    result = LiveResult(
                        code=code, score=score, correct=correct,
                        rows=tuple(rows), counts=summary(rows),
                        frame=image.copy(),
                        annotated=annotate_grading(aligned, rows, code),
                    )
                    with self._state_lock:
                        self._result = result
                        self._status = f'Đã tự động chấm mã đề {code}: {score:.2f}/10.'
            except (ValueError, cv2.error) as exc:
                with self._state_lock:
                    self._signature = None
                    self._streak = 0
                    self._status = f'Chưa quét được: {exc}'
        finally:
            self._work_lock.release()
