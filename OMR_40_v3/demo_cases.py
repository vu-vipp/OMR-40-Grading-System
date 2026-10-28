"""Reproducible synthetic test sheets; no student data."""
import cv2
import numpy as np
from omr import (CODES, DEFAULT_KEY, W, H, bubble_xy, blank_sheet, code_xy)

CASES = {
    'Dung_40_cau': '40 câu đúng, 10 điểm',
    'Sai_5_cau': '5 câu sai đáp án',
    'Bo_trong_3_cau': '3 câu không tô',
    'To_nhieu_2_cau': '2 câu tô hai ô',
    'To_mo_1_cau': '1 câu tô gần ngưỡng, cần kiểm tra',
    'Ma_de_102': 'Mã đề 102, 40 câu đúng theo đáp án mẫu',
    'Ma_de_103': 'Mã đề 103, 40 câu đúng theo đáp án mẫu',
    'Ma_de_104': 'Mã đề 104, 40 câu đúng theo đáp án mẫu',
    'Khong_to_ma_de': 'Không tô mã đề: phải từ chối chấm',
    'Hai_ma_de': 'Tô hai mã đề: phải từ chối chấm',
    'Thieu_moc_goc': 'Thiếu một mốc định vị',
    'Anh_trang': 'Ảnh trắng không có phiếu',
    'Anh_qua_nho': 'Ảnh nhỏ hơn mức yêu cầu',
    'Anh_qua_toi': 'Ảnh bị làm tối quá mức',
    'Anh_bi_nhoe': 'Ảnh bị làm nhòe nặng',
    'Anh_nghieng_nhe': 'Ảnh nghiêng/phối cảnh nhẹ',
}


def _fill(image, point, radius=13):
    cv2.circle(image, point, radius, (0, 0, 0), -1)


def create_case(name: str, key: str = DEFAULT_KEY) -> np.ndarray:
    if name not in CASES:
        raise ValueError('Không có tình huống thử nghiệm này.')
    image = blank_sheet()
    code = '101'
    if name.startswith('Ma_de_'):
        code = name.split('_')[-1]
    if name != 'Khong_to_ma_de':
        _fill(image, code_xy(CODES.index(code)))
    if name == 'Hai_ma_de':
        _fill(image, code_xy(1))
    for question, char in enumerate(key, 1):
        if name == 'Bo_trong_3_cau' and question in (2, 19, 38):
            continue
        index = 'ABCD'.index(char)
        if name == 'Sai_5_cau' and question in (1, 8, 15, 22, 36):
            index = (index + 1) % 4
        if name == 'To_mo_1_cau' and question == 17:
            _fill(image, bubble_xy(question, index), radius=6)
        else:
            _fill(image, bubble_xy(question, index))
        if name == 'To_nhieu_2_cau' and question in (3, 31):
            _fill(image, bubble_xy(question, (index + 1) % 4))
    if name == 'Thieu_moc_goc':
        cv2.rectangle(image, (0, 0), (120, 120), (255, 255, 255), -1)
    if name == 'Anh_trang':
        image[:] = 255
    if name == 'Anh_qua_nho':
        image = cv2.resize(image, (250, 350))
    if name == 'Anh_qua_toi':
        image = np.zeros_like(image) + 24
    if name == 'Anh_bi_nhoe':
        image = cv2.GaussianBlur(image, (101, 101), 40)
    if name == 'Anh_nghieng_nhe':
        src = np.float32([[0,0], [W-1,0], [W-1,H-1], [0,H-1]])
        dst = np.float32([[65,38], [W-55,75], [W-40,H-65], [40,H-30]])
        mat = cv2.getPerspectiveTransform(src,dst)
        image = cv2.warpPerspective(image, mat, (W,H), borderValue=(255,255,255))
    return image


def save_cases(folder):
    from pathlib import Path
    folder = Path(folder)
    folder.mkdir(exist_ok=True, parents=True)
    for name in CASES:
        cv2.imwrite(str(folder / f'{name}.png'), create_case(name))
