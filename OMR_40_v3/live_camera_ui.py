"""Optional Streamlit-WebRTC interface for automatic, continuous camera OMR.

The video-frame callback is deliberately free of Streamlit widget/session calls.
It only updates LiveScanner's lock-protected state; a Streamlit fragment polls it.
"""
from __future__ import annotations

import cv2
import pandas as pd
import streamlit as st

from live_scan import LiveScanner
from omr import normalize_key


def show_live_camera(student_id: str, codes, raw_keys, threshold: float, margin: float) -> None:
    """Show webcam and auto-grade a held sheet without clicking a capture button."""
    try:
        import av
        from streamlit_webrtc import WebRtcMode, webrtc_streamer
    except ImportError:
        st.error('Chưa cài thư viện quét camera liên tục.')
        st.code('python -m pip install -r requirements-camera.txt', language='bash')
        st.info('Sau khi cài, khởi động lại CHAY_WINDOWS.bat. Chế độ tải ảnh và chụp thủ công vẫn hoạt động.')
        return

    if not codes:
        st.warning('Hãy chọn nhóm mã đề trên thanh bên trước khi quét.')
        return
    try:
        selected_keys = {code: normalize_key(raw_keys[code]) for code in codes}
    except (ValueError, KeyError) as exc:
        st.error('Chưa có đáp án chuẩn hợp lệ cho tất cả mã đề đã chọn: ' + str(exc))
        return

    config = (tuple(codes), tuple((c, selected_keys[c]) for c in codes),
              float(threshold), float(margin))
    current = st.session_state.get('_live_scanner_state')
    if current is None or current[0] != config:
        scanner = LiveScanner(tuple(codes), selected_keys,
                              threshold=threshold, margin=margin)
        st.session_state['_live_scanner_state'] = (config, scanner)
    else:
        scanner = current[1]

    st.caption(
        'Nhấn START để bật camera một lần, giơ phiếu vào khung hình và giữ yên. '
        'Hệ thống tự đọc sau 3 khung hình hợp lệ liên tiếp, không cần bấm chụp. '
        'Sau khi chấm xong, bấm “Quét bài tiếp theo” để nhận phiếu khác.'
    )
    st.info('Camera cần quyền truy cập trình duyệt. Dùng localhost hoặc trang HTTPS để camera hoạt động.')
    if st.button('🔄 Quét bài tiếp theo', key='live_scan_reset'):
        scanner.reset()

    def on_frame(frame):
        image = frame.to_ndarray(format='bgr24')
        scanner.process_frame(image)
        _, n, result = scanner.snapshot()
        output = image.copy()
        if result is not None:
            label = f'DONE - CODE {result.code}: {result.score:.2f}/10'
            color = (20, 180, 40)
        else:
            label = f'AUTO SCAN - STABLE {n}/3'
            color = (0, 210, 255)
        cv2.rectangle(output, (8, 8), (min(image.shape[1] - 8, 520), 53), (20, 20, 20), -1)
        cv2.putText(output, label, (16, 38), cv2.FONT_HERSHEY_SIMPLEX,
                    .72, color, 2, cv2.LINE_AA)
        return av.VideoFrame.from_ndarray(output, format='bgr24')

    # Use WebRTC to transmit real camera frames to OpenCV; st.camera_input() only
    # returns a manual snapshot and therefore cannot perform unattended scanning.
    ctx = webrtc_streamer(
        key='omr-continuous-camera',
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=on_frame,
        media_stream_constraints={
            'video': {'width': {'ideal': 1280}, 'height': {'ideal': 960},
                      'facingMode': {'ideal': 'environment'}},
            'audio': False,
        },
        rtc_configuration={'iceServers': [{'urls': ['stun:stun.l.google.com:19302']}]},
        async_processing=True,
    )

    @st.fragment(run_every='1s')
    def live_result_panel():
        status, streak, result = scanner.snapshot()
        if result is None:
            if ctx.state.playing:
                st.info(status)
            else:
                st.caption('Nhấn START trong khung camera để bắt đầu quét.')
            return

        st.success(f'✅ Tự nhận diện mã đề {result.code}: {result.score:.2f}/10.')
        stats = st.columns(5)
        for col, (label, value) in zip(stats, [
            ('Mã đề', result.code),
            ('Điểm / 10', f'{result.score:.2f}'),
            ('Đúng', result.counts['Đúng']),
            ('Sai', result.counts['Sai']),
            ('Trống / nhiều', result.counts['Bỏ trống'] + result.counts['Tô nhiều']),
        ]):
            col.metric(label, value)
        left, right = st.columns(2)
        with left:
            st.image(cv2.cvtColor(result.frame, cv2.COLOR_BGR2RGB),
                     caption='Khung hình được hệ thống tự chọn', use_container_width=True)
        with right:
            st.image(cv2.cvtColor(result.annotated, cv2.COLOR_BGR2RGB),
                     caption='Phiếu đã căn chỉnh và chấm tự động', use_container_width=True)

        data = pd.DataFrame(list(result.rows))
        data.insert(0, 'Mã đề', result.code)
        data.insert(0, 'Số báo danh', student_id.strip() or 'Chưa nhập')
        st.dataframe(data, hide_index=True, use_container_width=True)
        file_data = data.to_csv(index=False).encode('utf-8-sig')
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button('⬇️ Xuất CSV', file_data,
                               f'ket_qua_camera_{result.code}.csv', 'text/csv',
                               key='live_scan_csv', use_container_width=True)
        with c2:
            ok, buffer = cv2.imencode('.png', result.annotated)
            if ok:
                st.download_button('⬇️ Ảnh chấm', buffer.tobytes(),
                                   f'nhan_dien_camera_{result.code}.png', 'image/png',
                                   key='live_scan_image', use_container_width=True)
        with c3:
            if st.button('💾 Lưu vào lịch sử', key='save_live_result',
                         use_container_width=True):
                st.session_state['history'].append({
                    'Số báo danh': student_id.strip() or 'Chưa nhập',
                    'Nguồn ảnh': 'Camera quét tự động',
                    'Mã đề': result.code, 'Điểm': result.score,
                    'Đúng': result.counts['Đúng'],
                    'Sai': result.counts['Sai'],
                    'Bỏ trống': result.counts['Bỏ trống'],
                    'Tô nhiều': result.counts['Tô nhiều'],
                    'Chưa rõ': result.counts['Chưa rõ'],
                    'Trạng thái': 'Đã chấm',
                })
                st.success('Đã lưu vào lịch sử phiên.')
        st.caption('Điểm chỉ được khóa khi 3 lần nhận diện giống nhau và không có câu tô chưa rõ. '
                   'Để quét tờ tiếp theo, bấm “Quét bài tiếp theo”.')

    live_result_panel()
