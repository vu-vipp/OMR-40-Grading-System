"""Verify that the real app routes live scan mode to the WebRTC component.

Uses a mocked Streamlit app entry, not a real browser integration test.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import types

from test_streamlit_smoke import _FakeStreamlit


def test_live_mode_is_available_and_uses_same_exam_codes(monkeypatch):
    fake = _FakeStreamlit('Dung_40_cau', source='🎥 Quét tự động bằng camera')
    monkeypatch.setitem(sys.modules, 'streamlit', fake)
    calls = []
    live_ui = types.ModuleType('live_camera_ui')
    live_ui.show_live_camera = lambda *args: calls.append(args)
    monkeypatch.setitem(sys.modules, 'live_camera_ui', live_ui)

    app = Path(__file__).parents[1] / 'app.py'
    spec = importlib.util.spec_from_file_location('_omr_live_wiring_app', app)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert len(calls) == 1
    student_id, codes, keys, threshold, margin = calls[0]
    assert student_id == ''
    assert codes == ('101','102','103','104')
    assert set(keys) >= set(codes)
    assert threshold == .24
    assert margin == .055
    assert not fake.camera_called  # The manual snapshot camera should not run.
    assert not fake.uploader_called
    assert fake.tab_labels == [
        '📝 Chấm bài', '📊 Lịch sử trong phiên', '📖 Hướng dẫn',
    ]
