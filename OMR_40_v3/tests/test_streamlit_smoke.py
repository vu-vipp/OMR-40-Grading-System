"""UI wiring smoke test without requiring Streamlit installation in the CI environment.
This is NOT a real browser/Streamlit integration test.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import types

import pytest


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


class _FakeStreamlit(types.ModuleType):
    def __init__(self, selected):
        super().__init__('streamlit')
        self.session_state = {}
        self.sidebar = _Element(self.session_state)
        self.selected = selected
        self.calls = []
    def tabs(self, names):
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
        return self.selected
    def file_uploader(self, *args, **kwargs):
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
def test_app_executes_with_mocked_ui(selected,kind,monkeypatch):
    mock = _FakeStreamlit(selected)
    monkeypatch.setitem(sys.modules, 'streamlit', mock)
    path = Path(__file__).parents[1] / 'app.py'
    spec = importlib.util.spec_from_file_location('_omr_mock_app',path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert kind in mock.calls
    if kind in ('warning','success'):
        assert 'dataframe' in mock.calls
    assert len([k for k in mock.session_state if k.startswith('answer_key_')]) == 4
