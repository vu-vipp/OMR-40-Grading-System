"""Streamlit UI smoke tests with uploaded images (no testing tab required).

These tests use a lightweight mock, not a real Streamlit browser session.
Synthetic image cases are kept in the test suite, not displayed on the UI.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import types

import cv2
import pytest

from demo_cases import create_case


class _Element:
    def __init__(self, state):
        self.state = state
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def metric(self, *a, **kw):
        return None
    def image(self, *a, **kw):
        return None
    def __getattr__(self, name):
        def fn(*args, **kwargs):
            return None
        return fn


class _ImageUpload:
    name = 'sample.png'
    def __init__(self, image):
        ok, data = cv2.imencode('.png', image)
        assert ok
        self.data = data.tobytes()
    def getvalue(self):
        return self.data


class _FakeStreamlit(types.ModuleType):
    def __init__(self, selected):
        super().__init__('streamlit')
        self.session_state = {}
        self.sidebar = _Element(self.session_state)
        self.upload = _ImageUpload(create_case(selected))
        self.calls = []
        self.tab_labels = []
    def tabs(self, names):
        self.tab_labels = list(names)
        return [_Element(self.session_state) for _ in names]
    def columns(self, number):
        return [_Element(self.session_state) for _ in range(number)]
    def expander(self, *args, **kwargs):
        return _Element(self.session_state)
    def text_area(self, label, value='', key=None, **kwargs):
        self.session_state.setdefault(key, value)
        return self.session_state[key]
    def text_input(self, *args, **kwargs):
        return ''
    def slider(self, label, min_value, max_value, value, **kwargs):
        return value
    def selectbox(self, label, options, **kwargs):
        return options[0]
    def multiselect(self, label, options, key=None, **kwargs):
        return self.session_state.get(key, options[:4])
    def file_uploader(self, *args, key=None, **kwargs):
        if key == 'uploaded_sheet':
            return self.upload
        return None
    def button(self, *args, **kwargs):
        return False
    def download_button(self, *args, **kwargs):
        self.calls.append('download')
        return False
    def success(self, *args, **kwargs):
        self.calls.append('success')
    def error(self, *args, **kwargs):
        self.calls.append('error')
    def warning(self, *args, **kwargs):
        self.calls.append('warning')
    def dataframe(self, *args, **kwargs):
        self.calls.append('dataframe')
    def __getattr__(self, name):
        def fn(*args, **kwargs):
            return None
        return fn


@pytest.mark.parametrize('selected,kind', [
    ('Dung_40_cau', 'success'),
    ('Bo_trong_3_cau', 'success'),
    ('To_nhieu_2_cau', 'success'),
    ('To_mo_1_cau', 'warning'),
    ('Khong_to_ma_de', 'error'),
    ('Anh_trang', 'error'),
])
def test_upload_grading_without_sample_tab(selected, kind, monkeypatch):
    mock = _FakeStreamlit(selected)
    monkeypatch.setitem(sys.modules, 'streamlit', mock)
    path = Path(__file__).parents[1] / 'app.py'
    spec = importlib.util.spec_from_file_location('_omr_mock_app', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert kind in mock.calls
    if kind in ('warning', 'success'):
        assert 'dataframe' in mock.calls
    assert mock.tab_labels == [
        '📝 Chấm bài', '📊 Lịch sử trong phiên', '📖 Hướng dẫn',
    ]
    assert '🧪 Kiểm thử mẫu' not in mock.tab_labels
    assert len([k for k in mock.session_state if k.startswith('answer_key_')]) == 4
