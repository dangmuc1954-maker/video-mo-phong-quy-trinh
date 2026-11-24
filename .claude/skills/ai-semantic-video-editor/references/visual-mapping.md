# Minh họa video chỉ có lời thoại — mọi thể loại

Áp dụng cho mọi video **không có người dẫn trên màn hình, chỉ có giọng đọc**: kể chuyện, đạo lý, review/quảng cáo không KOC, giải thích, chú thích, so sánh, thông tin/tin tức, mẹo/hướng dẫn.

## 7 nguyên tắc chung

1. **Cảnh = VIDEO ĐỘNG** (clip Tool/Muse 10s), luôn có chuyển động mang nghĩa: vật đang được dùng, quá trình đang diễn ra, nhân vật đang làm gì đó. Ảnh tĩnh zoom nhẹ chỉ là dự phòng khi không tạo được video.
2. **Mỗi câu thoại = một cảnh.** Câu nói tới đâu, hình diễn tới đó. Một ý dài thì chia thành chuỗi cảnh nối tiếp (`continue_from_previous`).
3. **Hành động tả theo giây** (`beats`: 0–3s… 3–7s… 7–10s…). Khoảnh khắc chính phải nằm trong khoảng thời gian câu đó được đọc.
4. **Lời mỗi cảnh dài 7–10 giây** (~22–32 âm tiết). Câu ngắn hơn thì dồn hành động chính lên đầu clip, hoặc dùng `keep`.
5. **Ý trừu tượng thì dùng ẩn dụ có hành động; so sánh thì đối lập thấy bằng mắt** (hai bên cùng khung, hoặc hai cảnh liền nhau có bố cục giống nhau).
6. **Graphic là lớp phụ, không thay cảnh động.** Số liệu, danh sách, so sánh, chữ chốt chạy trên nền clip động, bật lên đúng từ khóa, và chỉ dùng số liệu có nguồn.
7. **Đồng nhất**: cùng nhân vật / sản phẩm / bối cảnh / phong cách xuyên suốt (`subjects`, `style`, ảnh tham chiếu khi có ảnh sản phẩm thật).

## Cách minh họa theo loại video

| Loại | Câu thoại kiểu | Cảnh động nên tạo | Graphic đi kèm |
|---|---|---|---|
| **Kể chuyện / cổ tích** | "Cô bé bước vào khu rừng…" | Nhân vật làm đúng hành động trong câu, máy quay theo nhân vật | Chữ chốt ở cao trào, bài học |
| **Đạo lý / châm ngôn** | "Đích đến ở ngay trước mắt nhưng ta lại quay lưng" | Ẩn dụ có hành động, chia theo câu (đào vàng bỏ cuộc, hai con đường) | Chữ chốt bài học, bảng so sánh hai lựa chọn |
| **Review / quảng cáo không KOC** | "Kem thấm nhanh, không bết dính" | Sản phẩm đang được dùng: bôi kem tan trên da, nước chảy qua, xoay 360°, cận chất liệu (macro) | Danh sách tick công dụng, số chạy giá, chú thích chỉ vào chi tiết |
| **Giải thích / khoa học / cơ chế** | "Khi nhiệt độ tăng, phân tử chuyển động nhanh hơn" | Hoạt hình quá trình: hạt chuyển động nhanh dần, mũi tên dòng chảy, cắt lớp bên trong vật | Chữ khóa thuật ngữ, biểu đồ khi có số |
| **Chú thích / phân tích chi tiết** | "Phần đế được làm từ cao su non" | Máy quay lia hoặc zoom tới đúng bộ phận đó đang hoạt động (đế giày uốn cong) | Chú thích có đường chỉ vào bộ phận |
| **So sánh A vs B** | "Loại A nóng sau 5 phút, loại B vẫn mát" | Hai bên chạy song song cùng khung (chia đôi màn hình) hoặc hai cảnh liền nhau cùng góc máy; kết quả khác nhau hiện rõ | Bảng so sánh, biểu đồ cột (có nguồn) |
| **Thông tin / tin tức / số liệu** | "Giá vàng tăng 3 phiên liên tiếp" | Cảnh minh họa động liên quan (thỏi vàng xếp chồng cao dần, đường phố, dòng người) | Số chạy, biểu đồ, chữ tiêu đề (bắt buộc ghi nguồn) |
| **Mẹo / hướng dẫn từng bước** | "Bước 2: rắc baking soda lên vết bẩn" | Tay đang làm đúng thao tác của bước đó; cảnh trước/sau ở bước cuối | Số thứ tự bước, danh sách tick |
| **Top / liệt kê** | "Thứ ba: …" | Mỗi mục một cảnh động riêng, cùng phong cách chuyển cảnh | Số thứ tự lớn bật lên đầu mỗi mục |
| **Lịch sử / tiểu sử** | "Năm 1945, …" | Tái hiện cảnh thời kỳ đó với nhân vật tượng trưng (không giả mạo ảnh tư liệu thật) | Mốc năm chạy số, bản đồ hoặc dòng thời gian |

## Bẫy hay gặp khi tạo cảnh
- **AI vẽ luôn tên nhân vật thành chữ** (ví dụ chữ "SON" lơ lửng trên đầu) khi prompt có dạng `SON = …`, như `make_prompts.py` vẫn ghép. Cách tránh: mô tả nhân vật trong `subjects` không mở đầu bằng tên viết hoa; thêm `no name labels, no words floating in the air` vào `negative`. Nếu clip vẫn dính chữ thì cắt bằng `keep` (chữ thường chỉ ở 1–2 giây đầu), hoặc tạo lại riêng cảnh đó với `prompt_override` tả nhân vật bằng lời ("a stick-figure young man with…").
- **Nhòe hoặc biến hình khi hai nhân vật chạm nhau** (ôm, bắt tay): ghi rõ `both bodies clearly separate and solid` và `no ghosting or morphing`; xem `_review.jpg`, cảnh nào nhòe thì tạo lại.
- Cảnh lỗi phải được tự sửa hoặc tạo lại XONG trước khi dựng và xuất (tạo giọng song song được).
- Tạo lại một cảnh: tạo storyboard phụ `_redo/storyboard.json` chỉ chứa cảnh đó → `tool_macro.py` → `tool_jobs.py collect` → chép clip mới đè vào `1-canh/`.

## Kiểm tra trước khi tạo cảnh (tự soát trong bảng duyệt)

- Đọc từng câu thoại và hỏi: **cảnh này có chuyển động diễn đúng câu đó không?** Nếu chỉ là cảnh đẹp chung chung thì viết lại `beats`.
- Có câu nào nói một điều mà hình không cho thấy không? (ví dụ "không bết dính" mà không có cảnh chạm tay vào thử.)
- Đối lập và so sánh đã thấy được bằng mắt chưa?
- Chạy `story_voice.py --provisional` để xem độ dài từng cảnh. Cảnh dưới 6 giây thì thêm lời hoặc dồn hành động lên đầu.
- Video có số liệu: số trên graphic phải khớp số trong lời đọc và có nguồn.

Mẫu tham khảo: `templates/dao-ly-an-du.storyboard.json` (đạo lý: đào vàng + hai con đường). Cùng khung đó dùng được cho review, so sánh, giải thích; chỉ thay `subjects`, `beats` và `graphic`.
