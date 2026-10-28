"""Regression suite: answer grading, error handling, image geometry, key validation."""
import cv2
import numpy as np
import pytest

from omr import (CODES, DEFAULT_KEY, NUM_QUESTIONS, SheetError, W, H,
                 bubble_xy, code_xy, blank_sheet, image_quality,
                 align_sheet, classify, normalize_key, grade, recognize, summary,
                 annotate_grading)
from demo_cases import CASES, create_case

EXPECTED = {
    'Dung_40_cau': (10, 40, 0, 0, 0, 0),
    'Sai_5_cau': (8.75, 35, 5, 0, 0, 0),
    'Bo_trong_3_cau': (9.25, 37, 0, 3, 0, 0),
    'To_nhieu_2_cau': (9.5, 38, 0, 0, 2, 0),
    'To_mo_1_cau': (9.75, 39, 0, 0, 0, 1),
    'Ma_de_102': (10, 40, 0, 0, 0, 0),
    'Ma_de_103': (10, 40, 0, 0, 0, 0),
    'Ma_de_104': (10, 40, 0, 0, 0, 0),
    'Anh_nghieng_nhe': (10, 40, 0, 0, 0, 0),
}


@pytest.mark.parametrize('case,expected', list(EXPECTED.items()))
def test_synthetic_case_results(case, expected):
    code, answers, ratios, overlay, aligned = recognize(create_case(case))
    rows, score, correct, pending = grade(answers, DEFAULT_KEY)
    counts = summary(rows)
    assert (score, correct, counts['Sai'], counts['Bỏ trống'], counts['Tô nhiều'], pending) == expected
    assert code == (case.split('_')[-1] if case.startswith('Ma_de_') else '101')
    assert len(answers) == 40
    assert len(ratios) == 40
    assert overlay.shape == (H, W, 3) and aligned.shape == (H, W, 3)
    assert len(rows) == NUM_QUESTIONS


@pytest.mark.parametrize('case', [
    'Khong_to_ma_de', 'Hai_ma_de', 'Thieu_moc_goc', 'Anh_trang',
    'Anh_qua_nho', 'Anh_qua_toi', 'Anh_bi_nhoe',
])
def test_invalid_images_rejected(case):
    with pytest.raises(SheetError):
        recognize(create_case(case))


@pytest.mark.parametrize('wrong_answer', ['', 'A'*39, 'A'*41, 'A'*39+'Z', '1'*40, 'A B C'])
def test_answer_keys_rejected(wrong_answer):
    with pytest.raises(ValueError):
        normalize_key(wrong_answer)


@pytest.mark.parametrize('valid', [DEFAULT_KEY, DEFAULT_KEY.lower(), ' '.join(DEFAULT_KEY),
                                   ','.join(DEFAULT_KEY), '\n'.join(DEFAULT_KEY)])
def test_answer_keys_accept_separators(valid):
    assert normalize_key(valid) == DEFAULT_KEY


def test_key_by_code_is_independent():
    different = 'DCBA' * 10
    answer_map = {code: (DEFAULT_KEY if code == '101' else different) for code in CODES}
    assert len(set(answer_map.values())) == 2
    code, answers, *_ = recognize(create_case('Ma_de_102'))
    assert code == '102'
    assert grade(answers, answer_map[code])[1] == 0
    assert grade(answers, answer_map['101'])[1] == 10


def test_empty_and_multi_scored_zero():
    answers = {i: DEFAULT_KEY[i-1] for i in range(1, 41)}
    answers[1], answers[2], answers[3] = 'TRONG', 'NHIEU', 'KHONG_RO'
    rows, score, correct, pending = grade(answers, DEFAULT_KEY)
    assert (score, correct, pending) == (9.25, 37, 1)
    assert [r['Kết quả'] for r in rows[:3]] == ['Bỏ trống', 'Tô nhiều', 'Chưa rõ']


def test_grade_rejects_missing_question():
    with pytest.raises(ValueError):
        grade({i: 'A' for i in range(1,40)}, DEFAULT_KEY)


def test_grade_rejects_unknown_answer():
    answers = {i: 'A' for i in range(1,41)}
    answers[4] = 'E'
    with pytest.raises(ValueError):
        grade(answers, DEFAULT_KEY)


@pytest.mark.parametrize('ratios,expected', [
    ([0,0,0,0], 'TRONG'),
    ([1,0,0,0], 0),
    ([0,1,0,0], 1),
    ([0,0,1,0], 2),
    ([0,0,0,1], 3),
    ([1,0,0,1], 'NHIEU'),
    ([0.24,0,0,0], 'KHONG_RO'),
    ([0.23,0,0,0], 'KHONG_RO'),
    ([0.27,0,0.27,0], 'NHIEU'),
    ([0.4,0.23,0,0], 'KHONG_RO'),
    ([0.4,0.1,0,0], 0),
])
def test_bubble_classification(ratios, expected):
    assert classify(ratios) == expected


@pytest.mark.parametrize('bad', [[], [1,2], [1,2,3,4,5]])
def test_classify_rejects_wrong_vector_length(bad):
    with pytest.raises(ValueError):
        classify(bad)


@pytest.mark.parametrize('question', [1,2,20,21,30,40])
@pytest.mark.parametrize('option', [0,1,2,3])
def test_bubble_positions_inside_canvas(question, option):
    x,y=bubble_xy(question,option)
    assert 30 < x < W-30 and 30 < y < H-30


@pytest.mark.parametrize('question,option', [(0,0),(41,0),(1,-1),(1,4)])
def test_invalid_bubble_positions(question,option):
    with pytest.raises(ValueError):
        bubble_xy(question,option)


def test_code_coordinates_distinct():
    assert len({code_xy(i) for i in range(4)}) == 4


def test_sheet_starts_blank_for_all_40_bubbles():
    # The inner fill ratio of each empty bubble should be near 0.
    im = blank_sheet()
    assert im.shape == (1400,1000,3)
    code, answers, *_ = recognize(create_case('Dung_40_cau'))
    assert code == '101' and all(c in 'ABCD' for c in answers.values())


def test_corrupted_color_image_rejected():
    for bad in (None, np.zeros((100,100),np.uint8), np.zeros((500,500,4),np.uint8)):
        with pytest.raises(SheetError):
            image_quality(bad)


def test_quality_stats_returned():
    quality = image_quality(create_case('Dung_40_cau'))
    assert quality['brightness'] > 100
    assert quality['contrast'] > 12
    assert quality['sharpness'] > 18


def test_jpg_round_trip():
    image = create_case('Dung_40_cau')
    ok, buff = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    assert ok
    decoded = cv2.imdecode(buff, cv2.IMREAD_COLOR)
    code, answers, *_ = recognize(decoded)
    assert code == '101'
    assert grade(answers,DEFAULT_KEY)[1] == 10


def test_png_round_trip():
    image = create_case('Sai_5_cau')
    ok, buff = cv2.imencode('.png',image)
    assert ok
    code, answers,*_ = recognize(cv2.imdecode(buff,cv2.IMREAD_COLOR))
    assert code == '101' and grade(answers,DEFAULT_KEY)[1] == 8.75


def test_annotation_keeps_image_size():
    code,answers,ratios,overlay,aligned=recognize(create_case('Sai_5_cau'))
    rows,*_ = grade(answers,DEFAULT_KEY)
    colored = annotate_grading(aligned,rows,code)
    assert colored.shape == aligned.shape
    assert not np.array_equal(colored,aligned)


def test_distinct_student_photo_cannot_be_decoded_as_blank_sheet():
    rng = np.random.default_rng(20)
    random_img = rng.integers(0,256,(1200,900,3),dtype=np.uint8)
    with pytest.raises(SheetError):
        recognize(random_img)


def test_default_key_40_exact():
    assert len(DEFAULT_KEY)==40 and set(DEFAULT_KEY)=={'A','B','C','D'}
    assert len(CODES)==4


def test_app_does_not_index_streamlit_method():
    from pathlib import Path
    source=(Path(__file__).parents[1]/'app.py').read_text('utf-8')
    assert 'session_state.keys[' not in source
    assert 'session_state[f\'answer_key_' in source
