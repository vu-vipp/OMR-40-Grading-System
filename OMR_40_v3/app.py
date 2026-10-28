"""Streamlit interface for a fixed-layout 40-question optical mark reader."""
from __future__ import annotations
import io

import cv2
import numpy as np
import pandas as pd
import streamlit as st

from omr import (
    CODES, DEFAULT_KEY, NUM_QUESTIONS, SheetError, annotate_grading,
    blank_sheet, grade, image_quality, normalize_code, normalize_key, recognize, summary,
)
from demo_cases import CASES, create_case
from code_config import load_config, save_config, parse_config, dump_config

st.set_page_config(page_title='OMR 40 | Chấm bài trắc nghiệm', page_icon='📋', layout='wide')
st.title('📋 NHẬN DIỆN VÀ CHẤM ĐIỂM BÀI THI TRẮC NGHIỆM')
st.caption('Bài tập lớn Thị giác máy tính · OpenCV + Streamlit · 40 câu · Quản lý nhiều mã đề')

if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'answer_keys' not in st.session_state:
    try:
        st.session_state['answer_keys'] = load_config()
    except (ValueError, OSError) as exc:
        st.session_state['answer_keys'] = {}
        st.error('Không mở được cấu hình mã đề lưu trên máy: ' + str(exc))
if 'sheet_codes' not in st.session_state:
    st.session_state['sheet_codes'] = list(st.session_state['answer_keys'])[:4]

with st.sidebar:
    st.header('⚙️ Cấu hình chấm thi')
    st.warning('Đáp án ABCD lặp lại của mã đề 101–104 CHỈ LÀ DEMO. Cần nhập đáp án thật trước khi chấm.')
    with st.expander('➕ Thêm / xóa mã đề', expanded=True):
        st.caption('Nhập mã đề gồm 3 chữ số (ví dụ 105, 205 hoặc 001) và 40 đáp án chuẩn.')
        new_code = st.text_input('Mã đề mới', placeholder='Ví dụ 105', key='new_exam_code')
        new_key = st.text_area('Đáp án chuẩn của mã đề mới', height=75, key='new_exam_key',
                               placeholder='40 ký tự A/B/C/D')
        if st.button('➕ Thêm mã đề', use_container_width=True):
            try:
                code = normalize_code(new_code)
                key = normalize_key(new_key)
                if code in st.session_state['answer_keys']:
                    raise ValueError(f'Mã đề {code} đã tồn tại.')
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state['answer_keys'][code] = key
                st.session_state[f'answer_key_{code}'] = key
                st.success(f'Đã thêm mã đề {code}. Hãy bấm Lưu cấu hình để giữ lại khi tắt máy.')
                st.rerun()
        options = ['— Không xóa —', *st.session_state['answer_keys']]
        to_delete = st.selectbox('Chọn mã đề muốn xóa', options, key='remove_exam_code')
        if st.button('🗑️ Xóa mã đã chọn', use_container_width=True):
            if to_delete == options[0]:
                st.info('Hãy chọn một mã đề cần xóa.')
            else:
                st.session_state['answer_keys'].pop(to_delete, None)
                st.session_state.pop(f'answer_key_{to_delete}', None)
                st.session_state['sheet_codes'] = [c for c in st.session_state['sheet_codes'] if c != to_delete]
                st.success('Đã xóa mã đề khỏi cấu hình trong phiên. Bấm Lưu cấu hình để ghi thay đổi.')
                st.rerun()
    with st.expander('🗝️ Đáp án chuẩn theo mã đề', expanded=True):
        for code, saved_key in list(st.session_state['answer_keys'].items()):
            field = f'answer_key_{code}'
            key = st.text_area(f'Mã đề {code} — 40 đáp án A/B/C/D',
                               value=saved_key, key=field, height=75)
            st.session_state['answer_keys'][code] = key

    valid_keys = {}
    invalid_codes = {}
    for code, raw_key in st.session_state['answer_keys'].items():
        try:
            valid_keys[code] = normalize_key(raw_key)
        except ValueError as exc:
            invalid_codes[code] = str(exc)
    if invalid_codes:
        st.error('Đáp án chưa hợp lệ ở mã: ' + ', '.join(invalid_codes))

    with st.expander('💾 Lưu / nạp danh sách mã đề', expanded=True):
        st.caption('Lưu trên máy chạy Streamlit; nên tải JSON để có bản sao dự phòng.')
        if st.button('💾 Lưu cấu hình trên máy', use_container_width=True):
            if invalid_codes or not valid_keys:
                st.error('Hãy sửa tất cả đáp án chưa hợp lệ trước khi lưu.')
            else:
                try:
                    save_config(valid_keys)
                    st.success(f'Đã lưu {len(valid_keys)} mã đề. Lần khởi động sau sẽ tự nạp lại.')
                except OSError as exc:
                    st.error('Không ghi được tệp cấu hình trên máy: ' + str(exc))
        if valid_keys and not invalid_codes:
            st.download_button('⬇️ Xuất danh sách mã đề JSON',
                               dump_config(valid_keys).encode('utf-8'),
                               'danh_sach_ma_de.json', 'application/json', use_container_width=True)
        imported = st.file_uploader('Nhập file JSON mã đề đã lưu', type=['json'], key='exam_codes_json')
        if st.button('📥 Nạp file JSON', use_container_width=True):
            if imported is None:
                st.warning('Chưa chọn file JSON.')
            else:
                try:
                    loaded = parse_config(imported.getvalue())
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    for code in list(st.session_state['answer_keys']):
                        st.session_state.pop(f'answer_key_{code}', None)
                    st.session_state['answer_keys'] = loaded
                    st.session_state['sheet_codes'] = list(loaded)[:4]
                    st.success('Đã nạp cấu hình. Hãy bấm Lưu cấu hình để giữ lại sau khi thoát.')
                    st.rerun()

    st.subheader('🖨️ Mẫu phiếu và nhóm mã đề')
    st.caption('Chọn tối đa 4 mã đề để in lên MỘT mẫu phiếu. Có thể tạo nhiều mẫu cho các nhóm mã đề khác nhau.')
    codes_on_sheet = st.multiselect('Mã đề trên phiếu đang chấm',
                                    options=list(st.session_state['answer_keys']),
                                    max_selections=4, key='sheet_codes')
    if not codes_on_sheet:
        st.error('Hãy chọn ít nhất 1 mã đề để in hoặc nhận diện.')
    else:
        st.caption('Thứ tự các mã đề ở đây phải khớp với mẫu phiếu đã in. Chương trình kiểm tra dấu xác minh để tránh chọn nhầm.')
        ok, png = cv2.imencode('.png', blank_sheet(tuple(codes_on_sheet)))
        if ok:
            st.download_button('⬇️ Tải mẫu phiếu theo mã đã chọn', png.tobytes(),
                               'mau_phieu_' + '_'.join(codes_on_sheet) + '.png',
                               'image/png', use_container_width=True)
    with st.expander('Tùy chỉnh nhận diện (nâng cao)'):
        threshold = st.slider('Ngưỡng nhận diện ô tô', min_value=.15, max_value=.55, value=.24, step=.01)
        margin = st.slider('Biên độ tô chưa rõ', min_value=.01, max_value=.12, value=.055, step=.005)
        st.caption('Nếu chưa quen, hãy giữ nguyên thông số mặc định.')

page_grade, page_test, page_history, page_help = st.tabs([
    '📝 Chấm bài', '🧪 Kiểm thử mẫu', '📊 Lịch sử trong phiên', '📖 Hướng dẫn',
])


def render_sheet(image: np.ndarray, source_label: str, student_id: str, save_key: str,
                 sheet_codes: tuple[str, ...], demo_mode: bool = False):
    """Render a result and optional save action; reject before displaying grade when unsafe."""
    try:
        quality = image_quality(image)
        code, answers, ratios, _, aligned = recognize(image, threshold, margin, codes=sheet_codes)
        # Demo luôn dùng đáp án mẫu. Chấm bài thật chỉ dùng đáp án được người dùng cấu hình.
        if demo_mode:
            key = DEFAULT_KEY
        else:
            if code not in st.session_state['answer_keys']:
                raise ValueError(f'Chưa có đáp án chuẩn của mã đề {code}.')
            key = normalize_key(st.session_state['answer_keys'][code])
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
                if not codes_on_sheet:
                    st.error('Chưa chọn nhóm mã đề trên phiếu.')
                else:
                    render_sheet(image, upload.name, student_id, 'upload', tuple(codes_on_sheet))
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
    render_sheet(demo_image, chosen, 'DEMO', 'demo', CODES, demo_mode=True)

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
1. Vào **Thêm / xóa mã đề** ở thanh bên: nhập mã mới gồm **3 chữ số** và **40 đáp án chuẩn** (A/B/C/D).
2. Bấm **Lưu cấu hình trên máy** để giữ mã đề sau khi đóng chương trình. Có thể xuất/nhập JSON để chuyển máy.
3. Ở **Mẫu phiếu và nhóm mã đề**, chọn từ **1 đến 4 mã đề** muốn in trên cùng phiếu, rồi tải mẫu mới.
4. In mẫu phiếu đúng tỉ lệ; điền SBD, tô đúng **một ô mã đề** và mỗi câu tối đa một ô.
5. Khi chấm, chọn **đúng nhóm và đúng thứ tự mã đề đã in** trước khi tải ảnh lên; chương trình sẽ kiểm tra dấu xác minh của phiếu để tránh chấm sai mã.
6. Chụp đủ 4 mốc, ảnh sáng và nét; tải ảnh JPG/PNG lên, xem kết quả và xuất CSV.
7. Nếu có câu **chưa rõ**, điểm chỉ tạm tính và phải kiểm tra thủ công trước khi công nhận.

**Lưu ý:** Mỗi tờ phiếu chỉ có tối đa **4 ô mã đề**, nhưng có thể tạo nhiều mẫu phiếu và lưu nhiều mã đề trên chương trình. Không thể tự viết một mã mới trên mẫu 101–104 rồi mong chương trình nhận ra; phải in mẫu mới đã cấu hình.

**Tương thích:** Vẫn chấm được phiếu 101–104 in từ phiên bản V3 cũ khi chọn đúng nhóm 101–104. Bản V4 có thêm dấu xác minh giúp phát hiện nhầm mẫu.

**Giới hạn:** Không đọc số báo danh viết tay; ảnh quá mờ, thiếu góc hoặc bị che dấu xác minh có thể bị từ chối. Cần thử trên phiếu giấy thực tế trước khi chấm điểm chính thức.
''')
