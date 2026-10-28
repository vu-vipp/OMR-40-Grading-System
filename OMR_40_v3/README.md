# OMR 40 V3 — Nhận diện và chấm điểm bài thi trắc nghiệm

**Đề tài Thị giác máy tính · Python + OpenCV + Streamlit · 40 câu · 4 mã đề 101/102/103/104**

## 1. Mới trong V3

- Sửa hoàn toàn lỗi `TypeError: 'method' object is not subscriptable` do dùng `st.session_state.keys[code]` ở bản V2: nay truy cập bằng `st.session_state[f'answer_key_{code}']`.
- Sắp xếp lại giao diện thành 4 tab: **Chấm bài**, **Kiểm thử mẫu**, **Lịch sử trong phiên**, **Hướng dẫn**.
- Cho phép **nhập đáp án chuẩn riêng biệt** cho bốn mã đề; kiểm tra đáp án đúng **40 ký tự A/B/C/D**.
- Có **16 ảnh kiểm thử mẫu** để tải xuống và chạy trực tiếp từ giao diện.
- Xử lý **đúng, sai, bỏ trống, tô nhiều, tô chưa rõ**, báo lỗi **ảnh quá nhỏ/tối/nhòe, thiếu mốc**, và mã đề không xác định.
- **Không tự chấm chính thức** khi có câu tô mờ: điểm hiển thị là **tạm tính, cần kiểm tra thủ công**.
- Tải ảnh gốc và xem ảnh căn chỉnh, đánh dấu câu đúng/sai; xuất CSV và ảnh nhận diện.
- Nhập **số báo danh thủ công** (chưa hỗ trợ OCR chữ/số viết tay).
- Lưu nhiều kết quả vào lịch sử của **phiên hiện tại**, xuất tổng hợp CSV (không phải cơ sở dữ liệu lâu dài).
- 89 bài test tự động, bao gồm 6 test giao diện **mô phỏng (mock)**.

## 2. Cài đặt trên Windows

### Cách 1 — Nhấp đúp file

1. Cài Python 3.10 trở lên (nên dùng Python 3.11 hoặc 3.12).
2. Giải nén ZIP **toàn bộ** vào một thư mục **mới**. Không ghi đè lẫn vào bản V2.
3. Nhấp đúp `CHAY_WINDOWS.bat` để cài thư viện và mở Streamlit.
4. Mở trình duyệt tại `http://localhost:8501` nếu Streamlit chưa tự mở.

### Cách 2 — Terminal

Trong thư mục chứa `app.py`, chạy:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**Lưu ý:** Đóng Streamlit cũ bằng `Ctrl+C` trước khi chạy phiên bản mới để tránh dùng lẫn mã nguồn từ V2 hoặc chiếm cổng 8501.

## 3. Hướng dẫn chấm bài

1. Tại thanh bên trái, nhập *đáp án chuẩn thực tế* cho từng mã đề. Đáp án **ABCD lặp lại** ban đầu chỉ dành cho ví dụ, tuyệt đối không coi là đáp án của đề thi thật.
2. Tải mẫu phiếu từ sidebar (`mau_phieu_40_cau.png`), in **đúng tỉ lệ khung hình**.
3. Tô 1 mã đề, tối đa 1 đáp án A/B/C/D cho mỗi câu. Viết tên và SBD vào ô giấy.
4. Chụp ảnh phiếu đủ cả 4 **mốc vuông đen** ở bốn góc, đủ sáng, nét và ít nghiêng.
5. Mở tab **Chấm bài**, nhập SBD (gõ tay), tải ảnh PNG/JPG.
6. Xem kết quả, hình minh họa và xuất kết quả CSV/ảnh nhận diện.
7. Các câu "Chưa rõ" yêu cầu kiểm tra bằng mắt. Ảnh lỗi hoặc mã đề không hợp lệ sẽ không được chấm.

## 4. Cách chạy test

Nhấp đúp `TEST_WINDOWS.bat`, hoặc:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Đã chạy **89 test đạt** trong môi trường kiểm thử cho thuật toán nhận diện, đáp án, kiểm soát lỗi, hình học phiếu, mã đề, mã hóa JPEG/PNG và 6 **UI mock smoke tests**. Giao diện thực tế vẫn cần chạy trên máy có Streamlit. Xem `KET_QUA_KIEM_THU.txt`.

## 5. 16 tình huống demo

`Dung_40_cau`, `Sai_5_cau`, `Bo_trong_3_cau`, `To_nhieu_2_cau`, `To_mo_1_cau`, `Ma_de_102`, `Ma_de_103`, `Ma_de_104`, `Khong_to_ma_de`, `Hai_ma_de`, `Thieu_moc_goc`, `Anh_trang`, `Anh_qua_nho`, `Anh_qua_toi`, `Anh_bi_nhoe`, `Anh_nghieng_nhe`.

Mỗi ảnh là dữ liệu **tổng hợp bằng code**. Những tình huống sai, trống và tô nhiều được chấm 0 ở câu tương ứng; những câu "Chưa rõ" cần kiểm tra thủ công; những ảnh/mã đề không hợp lệ phải từ chối chấm.

## 6. Cấu trúc dự án

```
OMR_40_v3/
├─ app.py                  # Giao diện Streamlit
├─ omr.py                  # Tạo mẫu phiếu, xử lý ảnh, nhận diện, chấm điểm
├─ demo_cases.py           # Tạo 16 tình huống ảnh thử nghiệm
├─ mau_phieu_40_cau.png    # Mẫu phiếu trắng để in
├─ demo/                   # 16 ảnh test tổng hợp và ảnh kết quả
├─ tests/                  # 89 bài test
├─ requirements.txt
├─ requirements-dev.txt
├─ CHAY_WINDOWS.bat
├─ TEST_WINDOWS.bat
└─ KET_QUA_KIEM_THU.txt
```

## 7. Giới hạn cần lưu ý

- Chỉ sử dụng đúng **mẫu phiếu 40 câu của chương trình này**; không hỗ trợ mẫu trắc nghiệm tùy ý.
- Mã đề giới hạn **101, 102, 103, 104**; số báo danh phải nhập thủ công.
- Các ngưỡng chất lượng ảnh là **kinh nghiệm**; ảnh chụp từ điện thoại ở các điều kiện ánh sáng/camera khác nhau cần kiểm tra thêm. Hệ thống không đảm bảo phát hiện mọi lỗi ảnh hay mọi nét tô nhạt.
- Chưa có kiểm thử thực tế bằng một tập ảnh phiếu giấy đã in/chụp; 89 test tự động không đại diện cho độ chính xác ngoài thực tế.
- Chưa có cơ sở dữ liệu và chưa có báo cáo Word ở phiên bản này theo yêu cầu ưu tiên code của người dùng.
- Hạn chế nhận diện orientation nếu ảnh bị xoay ngược 180 độ; nên chụp đúng chiều như mẫu.
