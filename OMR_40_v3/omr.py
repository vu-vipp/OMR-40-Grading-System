"""40-question fixed-layout OMR. No OCR or machine-learning model required."""
from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np

W, H = 1000, 1400
LETTERS = 'ABCD'
CODES = ('101', '102', '103', '104')
MARKERS = np.float32([[65, 65], [935, 65], [935, 1335], [65, 1335]])
NUM_QUESTIONS = 40
DEFAULT_KEY = LETTERS * 10

class SheetError(ValueError):
    """A sheet cannot safely be processed."""


def bubble_xy(question: int, option: int) -> tuple[int, int]:
    if not 1 <= question <= NUM_QUESTIONS or not 0 <= option < 4:
        raise ValueError('Vị trí câu/đáp án không hợp lệ')
    col, row = divmod(question - 1, 20)
    return 225 + 495 * col + 62 * option, 300 + row * 46


def code_xy(index: int) -> tuple[int, int]:
    return 330 + index * 115, 216


def blank_sheet() -> np.ndarray:
    im = np.full((H, W, 3), 255, np.uint8)
    for x, y in MARKERS.astype(int):
        cv2.rectangle(im, (x-19, y-19), (x+19, y+19), (0, 0, 0), -1)
    cv2.putText(im, 'OMR - 40 QUESTIONS', (270, 112), cv2.FONT_HERSHEY_SIMPLEX, .95, (0, 0, 0), 2)
    cv2.putText(im, 'NAME: ___________________________________', (126, 152), cv2.FONT_HERSHEY_SIMPLEX, .62, (0, 0, 0), 2)
    cv2.putText(im, 'STUDENT ID: _____________________________', (126, 182), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 0), 2)
    cv2.putText(im, 'EXAM CODE:', (126, 222), cv2.FONT_HERSHEY_SIMPLEX, .52, (0, 0, 0), 1)
    for k, code in enumerate(CODES):
        x, y = code_xy(k)
        cv2.circle(im, (x, y), 19, (0, 0, 0), 2)
        cv2.putText(im, code, (x - 22, y + 37), cv2.FONT_HERSHEY_SIMPLEX, .52, (0, 0, 0), 1)
    # One column header, instead of repeating letters over bubbles in adjacent rows.
    for col in (0, 1):
        for k, letter in enumerate(LETTERS):
            hx, _ = bubble_xy(1 + col * 20, k)
            cv2.putText(im, letter, (hx - 7, 275), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0), 1)
    # Every bubble is fixed by template coordinates; drawing and recognition share this geometry.
    for q in range(1, NUM_QUESTIONS + 1):
        x, y = bubble_xy(q, 0)
        cv2.putText(im, f'{q:02d}', (x - 83, y + 7), cv2.FONT_HERSHEY_SIMPLEX, .58, (0, 0, 0), 2)
        for k, letter in enumerate(LETTERS):
            bx, by = bubble_xy(q, k)
            cv2.circle(im, (bx, by), 19, (0, 0, 0), 2)
    cv2.putText(im, 'KEEP ALL FOUR SOLID CORNER MARKS VISIBLE', (190, 1278), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 0), 1)
    return im


def image_quality(image: np.ndarray) -> dict:
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        raise SheetError('Ảnh không hợp lệ. Chỉ hỗ trợ ảnh màu JPG/PNG.')
    height, width = image.shape[:2]
    if min(height, width) < 450:
        raise SheetError('Ảnh có độ phân giải quá thấp; cạnh ngắn phải từ 450 px.')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    contrast = float(gray.std())
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if brightness < 40:
        raise SheetError('Ảnh quá tối. Hãy chụp lại dưới ánh sáng tốt hơn.')
    if contrast < 12:
        raise SheetError('Ảnh thiếu tương phản hoặc không có nội dung phiếu hợp lệ.')
    if sharpness < 18:
        raise SheetError('Ảnh quá mờ/nhòe. Hãy lấy nét và chụp lại.')
    return {'brightness': round(brightness, 1), 'contrast': round(contrast, 1), 'sharpness': round(sharpness, 1), 'size': f'{width}x{height}'}


def _find_markers(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hh, ww = gray.shape
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    zones: list[list[tuple[float, float, float]]] = [[], [], [], []]
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if not (max(80., hh * ww * .00015) < area < hh * ww * .02):
            continue
        x, y, w, h = cv2.boundingRect(contour)
        if not (.70 < w / max(h, 1) < 1.32 and area / max(w * h, 1) > .74):
            continue
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        if cv2.mean(gray, mask=mask)[0] > 110:
            continue
        center_x, center_y = x + w / 2, y + h / 2
        # Four corner markers are expected to remain near the sheet's four corners.
        if center_x < ww * .28 and center_y < hh * .28:
            zones[0].append((center_x, center_y, area))
        elif center_x > ww * .72 and center_y < hh * .28:
            zones[1].append((center_x, center_y, area))
        elif center_x > ww * .72 and center_y > hh * .72:
            zones[2].append((center_x, center_y, area))
        elif center_x < ww * .28 and center_y > hh * .72:
            zones[3].append((center_x, center_y, area))
    if any(not zone for zone in zones):
        raise SheetError('Không tìm thấy đủ 4 mốc đen tại góc phiếu. Hãy chụp đầy đủ tờ giấy và thử lại.')
    points = np.float32([max(zone, key=lambda v: v[2])[:2] for zone in zones])
    # Reject implausible / collapsed quadrilaterals.
    quad_area = abs(float(cv2.contourArea(points)))
    if quad_area < hh * ww * .35:
        raise SheetError('Các mốc định vị quá gần nhau hoặc phiếu bị cắt. Hãy chụp lại.')
    return points


def align_sheet(image: np.ndarray) -> np.ndarray:
    image_quality(image)
    source = _find_markers(image)
    homography = cv2.getPerspectiveTransform(source, MARKERS)
    return cv2.warpPerspective(image, homography, (W, H), borderValue=(255, 255, 255))


def fill_ratio(binary: np.ndarray, x: int, y: int) -> float:
    if y < 13 or x < 13 or y + 13 >= binary.shape[0] or x + 13 >= binary.shape[1]:
        raise SheetError('Vị trí ô tô nằm ngoài khung ảnh.')
    yy, xx = np.ogrid[-12:13, -12:13]
    mask = xx * xx + yy * yy <= 144
    values = binary[y-12:y+13, x-12:x+13]
    return float(np.mean(values[mask] > 0))


def classify(ratios, threshold: float = .24, margin: float = .055):
    if len(ratios) != 4 or not 0 < threshold < 1 or margin < 0:
        raise ValueError('Tham số phân loại không hợp lệ.')
    hits = [i for i, ratio in enumerate(ratios) if ratio >= threshold]
    if len(hits) >= 2:
        return 'NHIEU'
    if any(abs(ratio - threshold) < margin for ratio in ratios):
        return 'KHONG_RO'
    if not hits:
        return 'TRONG'
    return hits[0]


def recognize(image: np.ndarray, threshold: float = .24, margin: float = .055):
    aligned = align_sheet(image)
    gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 12)
    annotated = aligned.copy()
    code_ratios = [fill_ratio(binary, *code_xy(k)) for k in range(4)]
    code_choice = classify(code_ratios, threshold, margin)
    if not isinstance(code_choice, int):
        raise SheetError('Không đọc được duy nhất mã đề: chưa tô, tô nhiều hoặc tô quá mờ. Không chấm phiếu này.')
    code = CODES[code_choice]
    answers, ratios_by_question = {}, {}
    for question in range(1, NUM_QUESTIONS + 1):
        ratios = [fill_ratio(binary, *bubble_xy(question, k)) for k in range(4)]
        choice = classify(ratios, threshold, margin)
        answer = LETTERS[choice] if isinstance(choice, int) else choice
        answers[question] = answer
        ratios_by_question[question] = [round(r, 3) for r in ratios]
        for option in range(4):
            x, y = bubble_xy(question, option)
            color = (0, 160, 0) if answer == LETTERS[option] else (0, 165, 255) if answer == 'KHONG_RO' else (175, 175, 175)
            cv2.circle(annotated, (x, y), 22, color, 2)
        if answer in ('TRONG', 'NHIEU', 'KHONG_RO'):
            x, y = bubble_xy(question, 0)
            cv2.putText(annotated, '!', (x-55, y+7), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 0, 255), 2)
    cv2.putText(annotated, f'CODE: {code}', (130, 120), cv2.FONT_HERSHEY_SIMPLEX, .8, (5, 100, 240), 2)
    return code, answers, ratios_by_question, annotated, aligned


def normalize_key(key: str) -> str:
    # Allow typical copy/paste of keys with spaces, commas, semicolons and line breaks.
    if not isinstance(key, str):
        raise ValueError('Đáp án chuẩn phải là chuỗi.')
    normalized = ''.join(char for char in key.upper() if char not in ' \t\n\r,;|-')
    if len(normalized) != NUM_QUESTIONS or any(char not in LETTERS for char in normalized):
        raise ValueError('Đáp án chuẩn phải gồm đúng 40 chữ cái A/B/C/D (có thể cách nhau bởi khoảng trắng).')
    return normalized


def grade(answers: dict[int, str], key: str):
    normalized_key = normalize_key(key)
    if set(answers) != set(range(1, NUM_QUESTIONS + 1)):
        raise ValueError('Bài thi phải có dữ liệu nhận diện đủ 40 câu.')
    rows = []
    for question in range(1, NUM_QUESTIONS + 1):
        got, expected = answers[question], normalized_key[question - 1]
        if got not in (*LETTERS, 'TRONG', 'NHIEU', 'KHONG_RO'):
            raise ValueError(f'Đáp án nhận diện không hợp lệ tại câu {question}.')
        status = ('Chưa rõ' if got == 'KHONG_RO' else
                  'Bỏ trống' if got == 'TRONG' else
                  'Tô nhiều' if got == 'NHIEU' else
                  'Đúng' if got == expected else 'Sai')
        rows.append({'Câu': question, 'Đáp án tô': got, 'Đáp án đúng': expected, 'Kết quả': status})
    correct = sum(row['Kết quả'] == 'Đúng' for row in rows)
    pending = sum(row['Kết quả'] == 'Chưa rõ' for row in rows)
    return rows, round(correct * 10 / NUM_QUESTIONS, 2), correct, pending


def summary(rows: list[dict]) -> dict[str, int]:
    labels = ('Đúng', 'Sai', 'Bỏ trống', 'Tô nhiều', 'Chưa rõ')
    return {label: sum(r['Kết quả'] == label for r in rows) for label in labels}


def annotate_grading(aligned: np.ndarray, rows: list[dict], code: str) -> np.ndarray:
    """Mark selected answers: green=correct, red=wrong, orange=unresolved, gray=blank/multi."""
    result = aligned.copy()
    colors = {
        'Đúng': (40, 155, 40), 'Sai': (30, 35, 235), 'Bỏ trống': (160, 160, 160),
        'Tô nhiều': (0, 125, 255), 'Chưa rõ': (0, 165, 255),
    }
    for row in rows:
        q, got, status = row['Câu'], row['Đáp án tô'], row['Kết quả']
        targets = ([LETTERS.index(got)] if got in LETTERS else list(range(4)))
        for idx in targets:
            cv2.circle(result, bubble_xy(q, idx), 22, colors[status], 3)
        if status != 'Đúng':
            x, y = bubble_xy(q, 0)
            cv2.putText(result, '!', (x-54, y+7), cv2.FONT_HERSHEY_SIMPLEX, .7, colors[status], 2)
    cv2.putText(result, f'EXAM CODE: {code}', (118, 120), cv2.FONT_HERSHEY_SIMPLEX, .8, (240, 85, 0), 2)
    return result
