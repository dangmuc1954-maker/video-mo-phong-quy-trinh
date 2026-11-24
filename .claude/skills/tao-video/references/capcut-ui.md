# Thao tác giao diện CapCut (desktop 9.8, máy anh, màn hình 1568×656 theo khung screenshot)

Đã thao tác thật ngày 06/11/2026. Toạ độ là toạ độ click trong khung screenshot đầy đủ. Lệch thì chụp lại màn hình rồi dò.

## Quyền & mở app
- `request_access ["CapCut", "capcut.exe"]`: cửa sổ CapCut thuộc tiến trình `capcut.exe` nên phải xin cả hai.
- `open_application "CapCut"` → `wait 6`. Có popup quảng cáo Pro thì bấm X ở (960, 211).
- Trang chủ: project mới nhất nằm đầu tiên trong mục "Dự án", ở (139, 357). Bấm 1 lần để mở → `wait 6`.
- Đóng: nút X ở (1560, 8). Lần 1 đóng project (tự lưu), lần 2 đóng trang chủ. Rồi kiểm tra `tasklist | grep -ci capcut` = 0.

## Màn hình chỉnh sửa
- Thanh công cụ trên (y=25): Phương tiện 23, Âm thanh 56, Văn bản 80, Nhãn dán 103, Hiệu ứng 128, **Chuyển tiếp 155**, Chú thích 183, **Bộ lọc 207**, Điều chỉnh 231
- Xem trước ở (555–1053, 36–316). Nút Xuất ở (1502, 7)
- Timeline: thước thời gian ở y≈368, 1s ≈ 6,1 px, bắt đầu x=84. Click ở y=430 để dời đầu phát. Các track từ trên xuống: bộ lọc y≈465, chữ y≈477, video y≈500
- Bấm vào một khối chữ → bảng bên phải có các tab Văn bản / Hiệu ứng động (1128, 25) / Dạng bàn…
  - Tab Văn bản: hàng "Kiểu mặc định" ở y=274 (ô 2 ở x=1133 là chữ ĐEN viền trắng; muốn trắng viền đen thì set bằng script)
  - Tab Hiệu ứng động: Vào / Ra (1317, 48) / Vòng lặp; ô hiệu ứng lưới 36px. Ô có kim cương tím là Pro
- Bộ lọc: rê chuột lên ảnh nhỏ → nút "+" ở góc dưới phải ảnh → thêm vào timeline tại đầu phát (dài 3s, script sẽ kéo ra hết video)
- Kéo chọn nhiều khối chữ trên timeline KHÔNG ăn → đừng chỉnh từng dòng trên giao diện, dùng `polish_draft.py`

## Học kiểu mới (chữ / hiệu ứng / bộ lọc / chuyển cảnh) rồi áp hàng loạt
1. Trên giao diện: chỉnh **1** dòng chữ hoặc thêm **1** bộ lọc / chuyển cảnh như ý.
2. Đóng project (X), đọc `draft_content.json` của project: `materials.texts[0].content`, `materials.material_animations`, track `filter` và `materials.effects`, `materials.transitions`.
3. Cập nhật `assets/capcut_style_pack.json`, rồi chạy `polish_draft.py` cho toàn bộ video.

## Xuất video (đã chạy thật trên 9.7.5)
1. Mở project → click vào vùng xem trước một lần → **`ctrl+e`**. Phím tắt chắc hơn nút Xuất, vì nút này có lúc bấm không ăn.
2. Hộp thoại xuất: mặc định 1080p, 30fps, mp4. Nơi lưu mặc định là `%LOCALAPPDATA%\CapCut\Videos\<Tên>.mp4`. KHÔNG đổi nơi lưu, vì hộp chọn thư mục không cho gõ đường dẫn.
2b. Nếu nút cuối hộp thoại ghi **"Mua gói Pro để xuất video"**: thường do công tắc **Luồng quang học** (có nhãn PRO, cuối mục Video) đang bật → TẮT công tắc đó (không bấm Mua), nút sẽ đổi lại thành **Xuất**. (Gặp 07/11/2026.)
3. Bấm **Xuất** (886, 466). 80s video mất khoảng 30s. Trong lúc xuất có quảng cáo Pro, cứ kệ nó.
4. Xuất lại cùng tên thì CapCut đặt tên `<Tên>(1).mp4` → luôn lấy file MỚI NHẤT (`ls -t … | head -1`). Chờ thêm khoảng 8s cho CapCut nhả file, rồi **chép** sang `projects/<slug>/2-xuat/` (chép chứ không chuyển, vì file có thể còn bị giữ) và ffprobe kiểm tra. Trích 4 khung hình ghép thành `_check.jpg` để xem.
5. Xuất xong CapCut hiện hộp "chia sẻ lên TikTok/YouTube": chỉ bấm **Đóng**, không đăng gì. Sau đó đóng project (X góc phải trên cửa sổ) để CapCut nhả file clip, rồi mới xoá được `1-canh`.
6. Có báo "Bạn đang sử dụng các tính năng Pro": KHÔNG bấm Mua hay Dùng thử. Bấm "Quay lại phần chỉnh sửa", nhờ anh đăng nhập Pro.

## Mở đúng project
- Trang chủ xếp project theo lần sửa gần nhất. Project vừa dựng bằng script CHƯA chắc đứng đầu: nhìn ảnh bìa hoặc tên dưới ô (zoom) trước khi bấm. Lỡ mở nhầm project (báo "Media Not Found") thì bấm Hủy rồi đóng.
- Popup quảng cáo Pro/Ultra hay hiện khi mở CapCut: bấm X ở (960, 210) trước khi bấm project.

## Lỗi phiên bản
- Báo "Cần cập nhật … phiên bản 9.8.0": project được lưu bằng bản mới hơn bản đang cài. KHÔNG bấm cập nhật. Tắt CapCut rồi chạy lại `build_capcut_draft.py --replace` + `polish_draft.py`. Script dùng mẫu tương thích có sẵn trong `assets/capcut_templates`.
- CapCut có thể tự cập nhật rồi chạy ngầm không hiện cửa sổ. Lúc đó đường dẫn exe đổi, phải `request_access ["capcut.exe"]` lại. Muốn tắt hẳn thì dùng `taskkill //IM CapCut.exe`, không được thì thêm `//F`, nhưng chỉ khi không có cửa sổ nào đang mở.
- Mở CapCut: `open_application "CapCut"`. Nếu báo lỗi đường dẫn thì chạy `cmd //c start "" "%LOCALAPPDATA%\CapCut\Apps\CapCut.exe"`.
