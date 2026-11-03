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
    def __init__(self, selected, source='📁 Tải ảnh từ máy', image_data=None):
        super().__init__('streamlit')
        self.session_state = {}
        self.sidebar = _Element(self.session_state)
        self.upload = _ImageUpload(create_case(selected)) if image_data is None else image_data
        self.source = source
        self.calls = []
        self.camera_called = False
        self.uploader_called = False
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
            self.uploader_called = True
            return self.upload if self.source == '📁 Tải ảnh từ máy' else None
        return None
    def radio(self, label, options, **kwargs):
        assert self.source in options
        return self.source
    def camera_input(self, label, **kwargs):
        self.camera_called = True
        return self.upload if self.source == '📷 Chụp bằng camera' else None
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


@pytest.mark.parametrize('source', ['📁 Tải ảnh từ máy', '📷 Chụp bằng camera'])
@pytest.mark.parametrize('selected,kind', [
    ('Dung_40_cau', 'success'),
    ('Bo_trong_3_cau', 'success'),
    ('To_nhieu_2_cau', 'success'),
    ('To_mo_1_cau', 'warning'),
    ('Khong_to_ma_de', 'error'),
    ('Anh_trang', 'error'),
])
def test_grade_with_upload_or_camera(selected, kind, source, monkeypatch):
    mock = _FakeStreamlit(selected, source=source)
    monkeypatch.setitem(sys.modules, 'streamlit', mock)
    path = Path(__file__).parents[1] / 'app.py'
    spec = importlib.util.spec_from_file_location('_omr_mock_app', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert kind in mock.calls
    assert mock.camera_called == (source == '📷 Chụp bằng camera')
    assert mock.uploader_called == (source == '📁 Tải ảnh từ máy')
    if kind in ('warning', 'success'):
        assert 'dataframe' in mock.calls
    assert mock.tab_labels == [
        '📝 Chấm bài', '📊 Lịch sử trong phiên', '📖 Hướng dẫn',
    ]
    assert '🧪 Kiểm thử mẫu' not in mock.tab_labels
    assert len([k for k in mock.session_state if k.startswith('answer_key_')]) == 4


@pytest.mark.parametrize('source', ['📁 Tải ảnh từ máy', '📷 Chụp bằng camera'])
def test_invalid_photo_is_rejected(source, monkeypatch):
    class _UnreadablePhoto:
        name = 'broken.jpg'
        def getvalue(self):
            return b'not a valid image'

    mock = _FakeStreamlit('Dung_40_cau', source=source, image_data=_UnreadablePhoto())
    monkeypatch.setitem(sys.modules, 'streamlit', mock)
    path = Path(__file__).parents[1] / 'app.py'
    spec = importlib.util.spec_from_file_location('_omr_bad_photo_app', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert 'error' in mock.calls
    assert 'dataframe' not in mock.calls


@pytest.mark.parametrize('source', ['📁 Tải ảnh từ máy', '📷 Chụp bằng camera'])
def test_oversize_photo_is_rejected(source, monkeypatch):
    class _LargePhoto:
        name = 'huge.jpg'
        def getvalue(self):
            return b'x' * (15 * 1024 * 1024 + 1)

    mock = _FakeStreamlit('Dung_40_cau', source=source, image_data=_LargePhoto())
    monkeypatch.setitem(sys.modules, 'streamlit', mock)
    path = Path(__file__).parents[1] / 'app.py'
    spec = importlib.util.spec_from_file_location('_omr_large_photo_app', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert 'error' in mock.calls
    assert 'dataframe' not in mock.calls


def test_camera_waits_for_snapshot(monkeypatch):
    mock = _FakeStreamlit('Dung_40_cau', source='📷 Chụp bằng camera')
    mock.upload = None
    monkeypatch.setitem(sys.modules, 'streamlit', mock)
    path = Path(__file__).parents[1] / 'app.py'
    spec = importlib.util.spec_from_file_location('_omr_no_snapshot_app', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert mock.camera_called
    assert 'dataframe' not in mock.calls
    assert 'error' not in mock.calls
