"""New exam codes, sheet verification, backward compatibility and persistence."""
from __future__ import annotations
import json
import cv2
import numpy as np
import pytest

from omr import (CODES, DEFAULT_KEY, SheetError, normalize_code, validate_sheet_codes,
                 blank_sheet, code_xy, bubble_xy, recognize, grade)
from code_config import validate_keys, parse_config, dump_config, load_config, save_config


def completed_sheet(codes, position=0, key=DEFAULT_KEY):
    im = blank_sheet(codes)
    cv2.circle(im, code_xy(position), 13, (0,0,0), -1)
    for q, answer in enumerate(key, 1):
        cv2.circle(im, bubble_xy(q, 'ABCD'.index(answer)), 13, (0,0,0), -1)
    return im


@pytest.mark.parametrize('code', ['001','105','205','999'])
def test_new_code_format(code):
    assert normalize_code(code) == code


@pytest.mark.parametrize('bad', ['', '10','1000','12A','1 05', 'abc', None, 105])
def test_bad_code_rejected(bad):
    with pytest.raises(ValueError):
        normalize_code(bad)


@pytest.mark.parametrize('codes', [(), ('105',)*2, ('101','102','103','104','105'), '105', ('x05',)])
def test_bad_sheet_groups(codes):
    with pytest.raises(ValueError):
        validate_sheet_codes(codes)


@pytest.mark.parametrize('codes,position,expected', [
    (('105',),0,'105'),
    (('105','205'),1,'205'),
    (('105','205','305'),2,'305'),
    (('105','205','305','405'),3,'405'),
    (('001','002','003','004'),0,'001'),
    (('999','998','997','996'),3,'996'),
])
def test_custom_sheet_recognized(codes,position,expected):
    code, answers, *_ = recognize(completed_sheet(codes,position),codes=codes)
    assert code == expected
    assert grade(answers,DEFAULT_KEY)[1] == 10


def test_mismatched_group_rejected_instead_of_wrong_key():
    im=completed_sheet(('105','205','305','405'),position=2)
    with pytest.raises(SheetError, match='Sai nhóm mã đề'):
        recognize(im,codes=('101','102','103','104'))
    with pytest.raises(SheetError,match='Sai nhóm mã đề'):
        recognize(im,codes=('105','205','306','405'))


def test_different_order_is_rejected():
    im=completed_sheet(('105','205'))
    with pytest.raises(SheetError,match='Sai nhóm mã đề'):
        recognize(im,codes=('205','105'))


def test_old_sheet_without_stamp_works_for_default_codes_only():
    im=completed_sheet(CODES)
    # Simulate a printed copy of the V3 layout, before checksum was introduced.
    cv2.rectangle(im,(120,1215),(850,1250),(255,255,255),-1)
    code, answers, *_ = recognize(im, codes=CODES)
    assert code=='101' and grade(answers,DEFAULT_KEY)[1]==10
    with pytest.raises(SheetError,match='mẫu phiếu cũ'):
        recognize(im,codes=('105','205','305','405'))


def test_tampered_signature_rejected():
    codes=('105','205','305','405')
    im=completed_sheet(codes)
    cv2.rectangle(im,(810,1210),(840,1250),(255,255,255),-1)
    with pytest.raises(SheetError,match='dấu xác minh'):
        recognize(im,codes=codes)


def test_custom_sheet_after_perspective_transformation():
    codes=('105','205','305','405')
    im=completed_sheet(codes,position=1)
    src=np.float32([[0,0],[999,0],[999,1399],[0,1399]])
    dst=np.float32([[45,40],[950,73],[975,1360],[22,1320]])
    warped=cv2.warpPerspective(im,cv2.getPerspectiveTransform(src,dst),(1000,1400),
                               borderValue=(255,255,255))
    code,answers,*_=recognize(warped,codes=codes)
    assert code=='205' and grade(answers,DEFAULT_KEY)[1]==10


def test_config_roundtrip(tmp_path):
    config={'101':DEFAULT_KEY,'105':'DCBA'*10,'001':'A'*40}
    target=tmp_path/'answer_keys_local.json'
    save_config(config,target)
    assert load_config(target)==config
    assert parse_config(dump_config(config))==config
    assert parse_config(json.dumps(config))==config


@pytest.mark.parametrize('invalid', [
    {'abc':DEFAULT_KEY}, {'105':'A'*39}, {'105':'E'*40},
    {}, [], 'bad', {'105':None},
])
def test_invalid_configs_rejected(invalid):
    with pytest.raises(ValueError):
        validate_keys(invalid)


def test_bad_json_and_storage_integrity(tmp_path):
    target=tmp_path/'answer_keys_local.json'
    save_config({'101':DEFAULT_KEY}, target)
    with pytest.raises(ValueError):
        save_config({'102':'not an answer key'},target)
    assert load_config(target)=={'101':DEFAULT_KEY}
    with pytest.raises(ValueError):
        parse_config('{invalid json')


def test_app_supports_selectable_codes_and_sheet_validation():
    from pathlib import Path
    source=(Path(__file__).parents[1]/'app.py').read_text('utf-8')
    assert 'max_selections=4' in source
    assert 'codes=sheet_codes' in source
    assert 'save_config(valid_keys)' in source
    assert 'demo_mode=True' in source
