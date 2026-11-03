# OMR 40 V3 — Nhận diện và chấm điểm bài thi trắc nghiệm

**Đề tài Thị giác máy tính · Python + OpenCV + Streamlit · 40 câu · 4 mã đề 101/102/103/104**

## 1. Mới trong V3

- Sửa hoàn toàn lỗi `TypeError: 'method' object is not subscriptable` do dùng `st.session_state.keys[code]` ở bản V2: nay truy cập bằng `st.session_state[f'answer_key_{code}']`.
- Giao diện có 3 tab: **Chấm bài**, **Lịch sử trong phiên**, **Hướng dẫn** (đã ẩn phần kiểm thử mẫu khỏi giao diện).
- Cho phép **nhập đáp án chuẩn riêng biệt** cho bốn mã đề; kiểm tra đáp án đúng **40 ký tự A/B/C/D**.
- Bộ **16 ảnh kiểm thử mẫu** chỉ được lưu trong thư mục `demo/` và dùng qua bộ test; không hiển thị trên giao diện chấm thi.
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
5. Mở tab **Chấm bài**, nhập SBD (gõ tay), chọn **Tải ảnh từ máy** hoặc **Chụp bằng camera**. Chụp rõ cả 4 góc của phiếu.
6. Xem kết quả, hình minh họa và xuất kết quả CSV/ảnh nhận diện.
7. Các câu "Chưa rõ" yêu cầu kiểm tra bằng mắt. Ảnh lỗi hoặc mã đề không hợp lệ sẽ không được chấm.

## 4. Cách chạy test

Nhấp đúp `TEST_WINDOWS.bat`, hoặc:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Đã chạy **89 test đạt** trong môi trường kiểm thử cho thuật toán nhận diện, đáp án, kiểm soát lỗi, hình học phiếu, mã đề, mã hóa JPEG/PNG và 6 **UI mock smoke tests**. Giao diện thực tế vẫn cần chạy trên máy có Streamlit. Xem `KET_QUA_KIEM_THU.txt`.

## 5. 16 tình huống kiểm thử (không hiển thị trên giao diện)

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


## 8. Mới trong V4 — Tự thêm mã đề (101, 105, 205, 999, ...)

- Vào thanh bên **Thêm / xóa mã đề**, nhập mã đề đúng **3 chữ số** và đủ **40 ký tự A/B/C/D**; bấm **Thêm mã đề**.
- Có thể nhập thêm nhiều mã đề, sửa đáp án riêng và xóa mã không dùng.
- Bấm **Lưu cấu hình trên máy** để ghi vào `answer_keys_local.json` (đã đưa vào `.gitignore` để **không đẩy đáp án lên GitHub**). Có thể **xuất JSON / nhập JSON** để sao lưu hay chuyển máy; định dạng JSON bản V3 cũng được hỗ trợ.
- Tại mục **Mẫu phiếu và nhóm mã đề**, chọn **từ 1 đến 4 mã đề**, đúng thứ tự mong muốn, rồi tải mẫu phiếu để in. Muốn nhóm khác thì tạo mẫu mới. Đây là giới hạn **4 ô trên mỗi tờ giấy**, không giới hạn tổng mã đề được lưu.
- Trước khi chấm, chọn **đúng nhóm mã đề đã in**. Mẫu V4 có **dấu xác minh 24 bit** và chương trình sẽ từ chối chấm nếu chọn sai nhóm, tránh chấm nhầm giữa các mã có cùng vị trí ô tô.
- **Phiếu 101/102/103/104 in từ V3 cũ** vẫn có thể nhận diện khi chọn đủ nhóm mặc định. Không thể tự viết mã mới lên phiếu V3 cũ rồi dùng như phiếu mã mới; cần in mẫu mới.
- Tab **Kiểm thử mẫu** đã được bỏ khỏi giao diện theo yêu cầu; bộ test tự động và ảnh tổng hợp vẫn được giữ trong mã nguồn để kiểm tra thuật toán. Các đáp án ABCD lặp lại vẫn chỉ là dữ liệu demo.

### Ví dụ

Thêm mã đề `105` và `205`, chọn nhóm `101, 105, 205`, tải/in mẫu phiếu mới. Khi học sinh tô một trong ba ô mã đề, chương trình nhận diện đúng mã đã tô và lấy bộ đáp án riêng. Nếu chọn nhầm nhóm `101, 102, 103, 104`, chương trình sẽ báo **sai nhóm mã đề** chứ không âm thầm chấm nhầm.

### Kiểm thử

Chạy `TEST_WINDOWS.bat` hoặc `python -m pytest -q tests`. Bộ kiểm thử bao gồm ảnh tổng hợp và không thay thế kiểm thử thực tế với phiếu giấy và ảnh chụp điện thoại.


## 9. Chụp ảnh phiếu trực tiếp bằng camera

- Mở **Chấm bài** → **Chụp bằng camera** → cấp quyền camera cho Chrome/Edge → đưa **toàn bộ phiếu với 4 mốc đen** vào khung hình → chụp ảnh.
- Streamlit sẽ đưa ảnh chụp vào **cùng thuật toán OpenCV** như khi tải tệp JPG/PNG lên: kiểm tra ảnh, căn chỉnh, nhận diện mã đề và 40 câu, đối chiếu đáp án, xuất kết quả.
- Chọn **Tải ảnh từ máy** nếu không có webcam hoặc muốn sử dụng ảnh chụp sẵn. Không thay đổi bộ đáp án, mẫu phiếu hoặc cách tính điểm.
- Camera dùng quyền truy cập của **trình duyệt**; trên máy tính địa chỉ `http://localhost:8501` hoặc `http://localhost:8502` thường hoạt động. Truy cập từ điện thoại bằng HTTP qua địa chỉ IP mạng LAN có thể bị trình duyệt từ chối camera vì không phải nguồn an toàn; khi đó tải ảnh chụp sẵn hoặc dùng HTTPS.
- Chức năng hiện là **chụp một ảnh rồi chấm**, **không** tự quét liên tục từ luồng video.
- Có test mô phỏng camera (ảnh hợp lệ, chưa chụp, ảnh lỗi, ảnh quá lớn), nhưng vẫn cần thử webcam/trình duyệt thật và phiếu in thật để đánh giá độ chính xác.


## 10. V5 — Quét và chấm tự động khi giơ phiếu trước camera (không bấm chụp)

V5 thêm lựa chọn **🎥 Quét tự động bằng camera**, bên cạnh **📁 Tải ảnh từ máy** và **📷 Chụp bằng camera** trước đây.

### Cách sử dụng

1. Nhập đáp án chuẩn và chọn đúng nhóm mã đề ở sidebar. In mẫu phiếu của nhóm đã chọn.
2. Mở tab **Chấm bài** → chọn **🎥 Quét tự động bằng camera**.
3. Nhấn **START** trong khung video (bắt buộc một lần để cấp quyền webcam từ trình duyệt).
4. Đưa tờ phiếu đã tô vào khung hình, giữ cho **đủ 4 mốc đen** nằm trong ảnh. Không cần nhấn nút chụp.
5. Chương trình chạy OpenCV khoảng mỗi 0,6 giây, chỉ chấp nhận kết quả khi nhận được **3 lần đọc liên tiếp giống nhau**, không có câu **chưa rõ**.
6. Khi nhận diện ổn định, kết quả mã đề, điểm, ảnh được đánh dấu và bảng đúng/sai tự xuất hiện. Có thể xuất CSV/PNG và lưu vào lịch sử phiên.
7. Muốn chấm bài khác, bấm **Quét bài tiếp theo**, thay tờ giấy và tiếp tục giữ ổn định trước camera. Nút này không phải nút chụp; nó chỉ mở khóa một lượt quét mới để tránh chấm trùng.

### Cài đặt

Trên Windows, file `CHAY_WINDOWS.bat` sẽ **thử cài** gói WebRTC bổ sung nhưng vẫn chạy ứng dụng nếu cài add-on thất bại. Nếu camera tự động báo thiếu thư viện, mở CMD trong thư mục `OMR_40_v3` rồi chạy:

```cmd
py -m pip install -r requirements-camera.txt
```

Sau đó chạy lại `CHAY_WINDOWS.bat`. Thư viện cho chế độ quét liên tục: `streamlit-webrtc`, cùng phụ thuộc `av` và các thư viện video liên quan.

- Chế độ webcam liên tục được xử lý qua WebRTC; **không cần chụp ảnh từng lần**, khác với `st.camera_input()`.
- Camera trong trình duyệt thường hoạt động tại `http://localhost:8501` hoặc `http://localhost:8502`; với điện thoại truy cập qua IP LAN HTTP, có thể phải dùng HTTPS để được cấp quyền camera.
- Nếu camera hoặc đường WebRTC không hoạt động, vẫn có thể dùng **Tải ảnh** hoặc **Chụp bằng camera** như trước.
- Trong chế độ quét tự động, kết quả được giữ lại cho đến khi bấm **Quét bài tiếp theo**; điều này giúp tránh ghi trùng khi giữ nguyên một tờ giấy trước camera.
- Để tránh chấm nhầm, phiếu có câu **tô chưa rõ** sẽ không được xác nhận tự động. Các câu bỏ trống hoặc tô nhiều vẫn tính 0 điểm theo quy tắc hiện có.
- **Kiểm thử:** Module xử lý ổn định khung hình có các test cho ảnh demo, ảnh sai, debounce, ảnh mờ/không rõ và quét lại. Tuy nhiên, video WebRTC và phiếu in giấy cần được thử bằng camera thật trước khi dùng chính thức.


## 11. Camera lật ngược / bị mờ – điều chỉnh trực tiếp trong chế độ quét tự động

Trong **🎥 Quét tự động bằng camera**:
- **Ưu tiên camera nào?** Chọn **Camera sau / camera ngoài** (phù hợp điện thoại) hoặc **Camera trước / webcam**. Trên máy chỉ có 1 webcam thì hai lựa chọn có thể cùng dùng một thiết bị. Việc chọn camera là yêu cầu ưu tiên cho trình duyệt, không bảo đảm có đủ phần cứng.
- **Hướng hình camera:** Chọn **Giữ nguyên**, **Lật ngang (đảo gương)**, **Lật dọc**, hoặc **Xoay 180°**. Hình được chỉnh cả trước khi đưa vào OpenCV, không chỉ lật phần xem trước; vì vậy mốc phiếu và chữ sẽ được đọc theo hướng đã chọn.
- **Độ phân giải yêu cầu:** Mặc định **Full HD 1920×1080** (nếu webcam/browser hỗ trợ); tùy chọn **HD 1280×720** khi máy yếu hoặc video chậm. Trong khung video hiển thị **VIDEO: W×H** để biết độ phân giải thực tế.
- **Làm nét hình xem trước:** Tăng sắc cạnh hình người dùng nhìn thấy, **không ảnh hưởng ảnh dùng để chấm**, **không khôi phục chi tiết** khi webcam không lấy nét được. Nếu vẫn mờ: lau ống kính, bổ sung ánh sáng, thay khoảng cách cầm phiếu, giữ camera/giấy ổn định hoặc dùng camera sau điện thoại có lấy nét tốt.
- Sau khi đổi nguồn camera, hướng hình hoặc độ phân giải, trình duyệt có thể yêu cầu nhấn START lại để khởi động luồng video mới. Không cần bấm chụp mỗi bài.
- Camera mặc định của laptop thường không có khả năng tự động lấy nét ở khoảng cách gần. Đừng dí phiếu quá sát ống kính; hãy đưa tờ giấy vào vùng nét, đủ 4 mốc đen rồi giữ yên cho đến khi nhận diện.

**An toàn chấm điểm:** Chỉ lật/xoay dữ liệu video thật khi người dùng chọn tương ứng. Chức năng tô rõ/tô mờ, phát hiện mã đề, chấm điểm và xuất kết quả vẫn do thuật toán OMR cũ xử lý.


## 12. Sửa lỗi “Không đọc được duy nhất mã đề” khi ảnh camera có giấy bị cong/lệch nhẹ

Nếu ảnh đã tìm được đủ bốn mốc nhưng báo **không đọc được duy nhất mã đề** dù chỉ tô một ô, lỗi có thể do tờ giấy bị cong khiến tâm vòng tròn thực tế không nằm đúng tọa độ tính từ bốn mốc góc. Khi đó vùng lấy mẫu cũ bị lệch sang **đường viền vòng tròn chưa tô**, tạo ra tỷ lệ điểm ảnh giả gần ngưỡng.

- `omr.py::_calibrate_bubble_centers()` dùng OpenCV Hough Circle Transform tìm tâm 4 ô mã đề và 160 ô trả lời trên ảnh đã căn chỉnh.
- Chỉ dùng tâm đo từ ảnh nếu tìm thấy ít nhất 148/164 ô với hình học hợp lệ, cả bốn ô mã đề; nếu không đạt điều kiện, giữ cách lấy mẫu tọa độ chuẩn để tương thích ảnh cũ.
- Cả nhận diện mã đề, tính tỷ lệ tô của 40 câu và vòng đánh dấu kết quả đều theo tâm được hiệu chỉnh.
- **Không** bỏ kiểm tra tô nhiều, tô quá mờ, thiếu mã đề hay dấu xác minh mẫu phiếu.
- Có test ảnh tổng hợp bị uốn cong nhẹ, in thẳng bình thường và trường hợp tô hai mã đề / không tô mã đề.

Khi chưa chấm được ảnh thật, hãy giữ nguyên ảnh JPG/PNG gốc (không chỉ ảnh màn hình) và chụp thông báo lỗi đầy đủ để kiểm tra. Nên thử cả **Tải ảnh từ máy** và **Quét camera tự động**, dùng mẫu phiếu do ứng dụng phát hành.
