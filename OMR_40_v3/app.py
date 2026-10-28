"""Streamlit interface for a fixed-layout 40-question optical mark reader."""
from __future__ import annotations
import io
import json

import cv2
import numpy as np
import pandas as pd
import streamlit as st

from omr import (
    CODES, DEFAULT_KEY, NUM_QUESTIONS, SheetError, annotate_grading,
    blank_sheet, grade, image_quality, normalize_key, recognize, summary,
)
from demo_cases import CASES, create_case

st.set_page_config(page_title='OMR 40 | Chấm bài trắc nghiệm', page_icon='📋', layout='wide')
st.title('📋 NHẬN DIỆN VÀ CHẤM ĐIỂM BÀI THI TRẮC NGHIỆM')
st.caption('Bài tập lớn Thị giác máy tính · OpenCV + Streamlit · 40 câu · 4 mã đề')

if 'history' not in st.session_state:
    st.session_state['history'] = []

with st.sidebar:
    st.header('⚙️ Cấu hình chấm thi')
    st.warning('Các đáp án ABCD lặp lại bên dưới CHỈ LÀ ĐÁP ÁN DEMO. Phải thay bằng đáp án chính thức trước khi chấm bài thật.')
    with st.expander('Đáp án chuẩn theo từng mã đề', expanded=True):
        for code in CODES:
            st.text_area(
                f'Mã đề {code} — 40 ký tự A/B/C/D',
                value=DEFAULT_KEY,
                key=f'answer_key_{code}',
                height=85,
                help='Có thể nhập 40 ký tự liền nhau hoặc cách nhau bằng khoảng trắng.',
            )
    bad_keys = {}
    for code in CODES:
        try:
            normalize_key(st.session_state[f'answer_key_{code}'])
        except ValueError as exc:
            bad_keys[code] = str(exc)
    if bad_keys:
        st.error('Mã đề có đáp án chưa hợp lệ: ' + ', '.join(bad_keys))
    else:
        config = {code: normalize_key(st.session_state[f'answer_key_{code}']) for code in CODES}
        st.download_button(
            '⬇️ Tải cấu hình đáp án JSON',
            data=json.dumps(config, ensure_ascii=False, indent=2).encode('utf-8'),
            file_name='dap_an_4_ma_de.json', mime='application/json', use_container_width=True,
        )
    with st.expander('Tùy chỉnh nhận diện (nâng cao)'):
        threshold = st.slider('Ngưỡng nhận diện ô tô', min_value=.15, max_value=.55, value=.24, step=.01)
        margin = st.slider('Biên độ tô chưa rõ', min_value=.01, max_value=.12, value=.055, step=.005)
        st.caption('Nếu chưa quen, hãy giữ nguyên thông số mặc định.')
    ok, png = cv2.imencode('.png', blank_sheet())
    if ok:
        st.download_button('⬇️ Tải mẫu phiếu trắng 40 câu', png.tobytes(), 'mau_phieu_40_cau.png', 'image/png', use_container_width=True)

page_grade, page_test, page_history, page_help = st.tabs([
    '📝 Chấm bài', '🧪 Kiểm thử mẫu', '📊 Lịch sử trong phiên', '📖 Hướng dẫn',
])


def render_sheet(image: np.ndarray, source_label: str, student_id: str, save_key: str):
    """Render a result and optional save action; reject before displaying grade when unsafe."""
    try:
        quality = image_quality(image)
        code, answers, ratios, _, aligned = recognize(image, threshold, margin)
        key = normalize_key(st.session_state[f'answer_key_{code}'])
        rows, score, correct, pending = grade(answers, key)
    except (ValueError, cv2.error) as exc:
        st.error('⛔ Không thể chấm bài: ' + str(exc))
        st.info('Kiểm tra ảnh có đủ 4 mốc, có tô đúng một mã đề và sử dụng đúng mẫu phiếu của chương trình.')
        return

    counts = summary(rows)
    if pending:
        st.warning(f'Có {pending} câu tô chưa rõ. Điểm {score:.2f} chỉ là **TẠM TÍNH**; cần kiểm tra thủ công trước khi công nhận.')
    else:
        st.success(f'Đã nhận diện mã đề {code} và chấm đủ {NUM_QUESTIONS} câu.')

    metrics = st.columns(6)
    for col, (label, value) in zip(metrics, [
        ('Mã đề', code), ('Điểm /10', f'{score:.2f}' + (' *' if pending else '')),
        ('Đúng', counts['Đúng']), ('Sai', counts['Sai']),
        ('Bỏ trống', counts['Bỏ trống']), ('Tô nhiều / chưa rõ', counts['Tô nhiều'] + counts['Chưa rõ']),
    ]):
        col.metric(label, value)
    with st.expander('Chất lượng ảnh và trạng thái xử lý'):
        st.write(f"Kích thước: {quality['size']} · Độ sáng: {quality['brightness']} · Độ tương phản: {quality['contrast']} · Độ sắc nét: {quality['sharpness']}")
        st.write(f"**Trạng thái:** {'Chờ kiểm tra thủ công' if pending else 'Đã hoàn tất chấm tự động'}")
        if counts['Tô nhiều']:
            st.warning(f"Có {counts['Tô nhiều']} câu tô nhiều đáp án; tính 0 điểm/câu.")

    annotated = annotate_grading(aligned, rows, code)
    left, right = st.columns(2)
    with left:
        st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption='Ảnh gốc', use_container_width=True)
    with right:
        st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption='Ảnh đã căn chỉnh & đánh dấu kết quả', use_container_width=True)
    st.caption('Xanh: đúng · Đỏ: sai · Xám: bỏ trống · Cam: tô nhiều hoặc chưa rõ')

    frame = pd.DataFrame(rows)
    frame.insert(0, 'Mã đề', code)
    frame.insert(0, 'Số báo danh', student_id.strip() or 'Chưa nhập')
    if pending:
        frame['Trạng thái bài'] = 'Tạm tính / chờ kiểm tra'
    else:
        frame['Trạng thái bài'] = 'Đã chấm'
    st.dataframe(frame, hide_index=True, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button('⬇️ Xuất kết quả CSV', frame.to_csv(index=False).encode('utf-8-sig'),
                           f'chi_tiet_{code}.csv', 'text/csv', use_container_width=True, key=f'csv_{save_key}')
    with c2:
        ok, buff = cv2.imencode('.png', annotated)
        if ok:
            st.download_button('⬇️ Xuất ảnh nhận diện', buff.tobytes(), f'nhan_dien_{code}.png',
                               'image/png', use_container_width=True, key=f'png_{save_key}')
    with c3:
        if st.button('💾 Lưu vào lịch sử phiên', key=f'save_{save_key}', use_container_width=True):
            st.session_state['history'].append({
                'Số báo danh': student_id.strip() or 'Chưa nhập', 'Nguồn ảnh': source_label,
                'Mã đề': code, 'Điểm': score, 'Đúng': counts['Đúng'], 'Sai': counts['Sai'],
                'Bỏ trống': counts['Bỏ trống'], 'Tô nhiều': counts['Tô nhiều'],
                'Chưa rõ': counts['Chưa rõ'], 'Trạng thái': 'Tạm tính' if pending else 'Đã chấm',
            })
            st.success('Đã lưu vào lịch sử phiên. Mở tab “Lịch sử trong phiên” để xuất CSV tổng hợp.')


with page_grade:
    st.subheader('1. Tải ảnh bài thi đã tô')
    student_id = st.text_input('Số báo danh (nhập thủ công, không phải OCR)', placeholder='Ví dụ: 012345', key='sbd_upload')
    upload = st.file_uploader('Chọn ảnh JPG hoặc PNG có đủ 4 mốc đen', type=['jpg', 'jpeg', 'png'], key='uploaded_sheet')
    if upload is not None:
        if len(upload.getvalue()) > 15 * 1024 * 1024:
            st.error('Tệp quá lớn. Vui lòng dùng ảnh dưới 15 MB.')
        else:
            image = cv2.imdecode(np.frombuffer(upload.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                st.error('Không đọc được ảnh. Hãy thử tệp JPG/PNG khác.')
            else:
                render_sheet(image, upload.name, student_id, 'upload')
    else:
        st.info('Chưa có ảnh? Sang tab **Kiểm thử mẫu** để chạy ngay 16 tình huống demo.')

with page_test:
    st.subheader('2. Bộ ảnh kiểm thử tự động tạo')
    st.write('Chọn một trường hợp, xem ảnh và kết quả chạy thật của thuật toán. Các ảnh là dữ liệu tổng hợp, không phải ảnh bài thi thực tế.')
    chosen = st.selectbox('Tình huống kiểm thử', options=list(CASES), format_func=lambda x: f'{x} — {CASES[x]}')
    demo_image = create_case(chosen)
    ok, demo_buff = cv2.imencode('.png', demo_image)
    if ok:
        st.download_button('⬇️ Tải ảnh test này', demo_buff.tobytes(), f'{chosen}.png', 'image/png', key='demo_image_download')
    render_sheet(demo_image, chosen, 'DEMO', 'demo')

with page_history:
    st.subheader('3. Lịch sử chấm trong phiên hiện tại')
    if st.session_state['history']:
        table = pd.DataFrame(st.session_state['history'])
        st.dataframe(table, hide_index=True, use_container_width=True)
        st.download_button('⬇️ Xuất CSV tổng hợp', table.to_csv(index=False).encode('utf-8-sig'),
                           'tong_hop_cham_thi.csv', 'text/csv')
        if st.button('🗑️ Xóa lịch sử phiên'):
            st.session_state['history'] = []
            st.rerun()
    else:
        st.info('Chưa có kết quả nào được lưu. Sau khi chấm, bấm “Lưu vào lịch sử phiên”.')
    st.caption('Lịch sử chỉ tồn tại trong phiên Streamlit, không lưu vào cơ sở dữ liệu. Hãy xuất CSV trước khi đóng hoặc khởi động lại ứng dụng.')

with page_help:
    st.subheader('4. Quy trình sử dụng')
    st.markdown('''
1. Nhập **đáp án chính thức riêng cho từng mã đề** ở thanh bên trái; không dùng đáp án demo để chấm thật.
2. Tải mẫu phiếu trắng và in với tỷ lệ đúng (không bóp méo tỉ lệ khung hình).
3. Điền số báo danh, tô **đúng một mã đề**, mỗi câu tô tối đa một ô A/B/C/D.
4. Chụp đủ cả bốn mốc đen tại bốn góc; bảo đảm ảnh sáng, nét, không mất góc.
5. Tải ảnh lên, xem kết quả đúng/sai/trống/tô nhiều/chưa rõ và xuất CSV.
6. Nếu báo **tạm tính**, kiểm tra thủ công các câu chưa rõ; chưa sử dụng điểm làm kết quả chính thức.

**Giới hạn:** Chỉ nhận phiếu đúng mẫu; không đọc tên/số báo danh viết tay; ảnh chụp quá nghiêng,
che mốc, quá mờ, ánh sáng phức tạp có thể bị từ chối hoặc nhận diện chưa chính xác.
Nên kiểm chứng bằng phiếu giấy thật trước khi dùng chấm điểm chính thức.
''')
