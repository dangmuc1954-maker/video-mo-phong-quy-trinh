# Hook · vòng lặp mở · thumbnail (graphic v2, anh duyệt 10/11/2026)

Tiêu đề, thumbnail và 3 giây đầu phải **nói cùng một lời hứa**. Người xem bấm vì thumbnail, ở lại vì 3 giây đầu xác nhận đúng lời hứa đó, xem hết vì câu hỏi chưa được trả lời.

## 1. Hook 3 giây đầu: chọn 1 công thức theo thể loại

| Công thức | Câu mẫu | Hình trong 3 giây đầu |
|---|---|---|
| **Nghịch lý** | "Một hòn đảo phải mua nước để uống… nay giàu hơn cả nước Mỹ." | tranh/ảnh trước–sau, lia từ cái nghèo sang cái giàu, chữ lớn "GIÀU HƠN CẢ NƯỚC MỸ?" |
| **Con số sốc** | "19,7 cây số. 17 năm chờ đợi." | số khổng lồ đếm lên (`count`), năm chạy `year_roll` 2007 → 2024 |
| **Câu hỏi tò mò** | "Vì sao người Nhật sống thọ nhất thế giới?" | cận cảnh chủ thể + câu hỏi chữ lớn |
| **Kết quả trước** | "Video bạn đang xem không ai ngồi dựng." | khoe kết quả rồi mới kể cách làm |
| **Chi tiết lạ** | "Có một con đường ở Việt Nam chỉ dài 7 mét." | hình chi tiết lạ, khoanh vàng |
| **Đối đầu** | "Singapore và Mỹ: ai giàu hơn?" | thanh đua `race` |

Luật:
- Giây 0 đã có chuyển động và chữ. Không mở bằng logo, lời chào hay màn hình đen.
- Câu hook ≤ 15 từ, chứa 1 con số hoặc 1 nghịch lý. Số phải có nguồn (facts.json).
- Hook graphic dùng hình mạnh nhất của cả video: tranh Ảnh AI 16:9 hoặc ảnh/video thật.

## 2. Giữ người xem
- Cứ 5–8 giây có một móc mới: số mới, hình mới, nhãn mới bật lên đúng lúc đọc.
- **Vòng lặp mở** (`open_loop`): sau đoạn mở đầu, treo một câu hỏi lớn kèm các thẻ khoá ("BÍ QUYẾT #1…#3"), rồi trả lời dần trong video. Cuối video nhắc lại câu mở đầu ("Nhớ câu mở đầu chứ?") để khép vòng.
- Cao trào ở khoảng 70–85% thời lượng, dồn hiệu ứng mạnh nhất vào đây.

## 3. Thumbnail: `scripts/thumbnail.py` làm 2–3 phương án

| Layout | Khi nào | Thành phần |
|---|---|---|
| `split` | trước–sau, xưa–nay, A đối B | ảnh chia đôi, nhãn năm 2 bên, 2 dòng chữ dưới (trắng + vàng) |
| `number` | con số là điểm sốc | số khổng lồ vàng, 2 dòng chữ trắng, nhãn đỏ, vòng tròn quanh chủ thể |
| `concept` | ý tưởng lạ (thành phố trong ly nước…) | tranh concept Ảnh AI, chữ bên trái, mũi tên + vòng tròn chỉ vào chi tiết, cờ quốc gia |

Luật:
- 1 chủ thể rõ, chiếm ≥ 40% khung, có cảm xúc mạnh (mặt người, hoặc vật thể gây tò mò).
- Chữ 3–6 từ, tối đa 2 dòng to, viền đen dày, dòng nhấn màu vàng `_..._`. Không lặp nguyên văn tiêu đề; thumbnail và tiêu đề bổ sung cho nhau.
- Màu bão hoà và tương phản cao. Vùng chữ có nền tối phía sau.
- Vòng tròn hoặc mũi tên chỉ khi có chi tiết cần chỉ.
- **Không câu view sai sự thật**: điều thumbnail hứa phải có trong video.
- Ảnh người thật chỉ từ nguồn đã công bố, có quyền dùng. Ảnh AI không giả làm ảnh thật của người có thật.
- Xem `render/_thumbs_check.jpg`: hàng dưới là cỡ hiển thị trên điện thoại, chữ vẫn phải đọc được. Đăng 2–3 phương án bằng tính năng **Thử nghiệm và so sánh** (Test & compare) của YouTube Studio.

## 4. Tranh minh hoạ cho hook và thumbnail (Ảnh AI)
- `storyboard["image_jobs"]` → `image_macro.py <sb> --auto --collect`. Prompt tả bố cục điện ảnh, ánh sáng, cảm xúc; ghi "16:9 wide, no text, no letters, no watermark".
- Dòng ảnh mới **thừa hưởng tỉ lệ của dòng trước** (hay là 9:16): đổi sang 16:9 cho các dòng mới trước khi bấm tạo. `gemini_wm.py` (tự chạy sau `--collect`) cảnh báo ảnh sai tỉ lệ và tự đẩy logo ngôi sao Gemini ra khỏi khung nếu job chưa bật xoá watermark (bản gốc giữ ở `*.orig.*`).
- Cảnh dùng tranh AI ghi rõ "Tranh minh hoạ" (`caption` của `quote`, hoặc `bg_source`). Không dùng tranh AI làm "bằng chứng" cho chuyện có thật.
