# Mode 2 — STORYTELLING (kể chuyện, đạo lý, giáo dục)

Mục tiêu: **lời kể nói gì, hình diễn đúng cái đó**, liền mạch như một bộ phim ngắn, có graphic động ở các điểm nhấn.

## 0. Nguyên tắc vàng: cảnh là VIDEO ĐỘNG diễn đúng lời kể (áp dụng cho MỌI video chỉ có lời thoại — xem thêm `visual-mapping.md`)

- Mỗi cảnh là **clip video chuyển động** (Tool/Muse, 10s) có nhân vật đang **làm hành động**. Không dùng ảnh tĩnh chỉ zoom nhẹ; ảnh tĩnh chỉ là phương án dự phòng khi không tạo được video.
- **Mỗi ẩn dụ chia thành một chuỗi cảnh, mỗi cảnh ứng với MỘT câu lời kể.** Câu nói tới đâu thì hình diễn tới đó: nói "gần tới vàng" thì thấy vàng ngay dưới mũi cuốc; nói "quay lưng bỏ đi" thì thấy nhân vật vứt cuốc bỏ đi.
- Tả hành động bằng `beats` (diễn biến theo giây: 0–3s… 3–7s… 7–10s…) để clip có mở đầu, cao trào, kết thúc khớp nhịp câu kể.
- **Độ dài lời kể ≈ độ dài hành động.** Cảnh bị cắt theo độ dài câu đọc (~3.2 âm tiết/giây), nên lời kể mỗi cảnh nên dài 7–10 giây (~22–32 âm tiết). Câu ngắn hơn thì đẩy khoảnh khắc chính lên đầu clip trong `beats`, hoặc đặt `keep` để lấy đúng đoạn có hành động chính. Chạy `story_voice.py --provisional` sau khi viết để xem độ dài từng cảnh: cảnh nào dưới 6 giây thì viết thêm lời kể.
- Cảnh cùng một ẩn dụ thì nối tiếp nhau (`continue_from_previous: true`): cùng nhân vật, cùng bối cảnh. Sang ẩn dụ mới thì mở chuỗi mới.
- Đối lập phải **thấy được bằng mắt**: chi tiết đánh lừa (ánh sáng trước ngõ cụt) và sự thật bị che (thành phố sau màn sương) đều phải hiện ra trong khung hình, máy quay lia hoặc kéo ra để lộ chúng đúng lúc lời kể nói tới.
- Nhân vật tượng trưng (người que, nhân vật tròn trắng, bóng người) được, miễn là giữ nguyên thiết kế ở mọi cảnh (`subjects` cố định).
- Mẫu đầy đủ: `templates/dao-ly-an-du.storyboard.json` (đào vàng bỏ cuộc + hai con đường).

## 1. Viết kịch bản (`templates/story-script.md`)

- Độ dài: 60s ≈ 180–200 âm tiết tiếng Việt (giọng đọc ~3.2 âm tiết/giây, có ngắt nghỉ).
- Cấu trúc: **Hook (0–3s)** → Bối cảnh → Xung đột/thử thách → Bước ngoặt → Kết quả → **Bài học** → (CTA).
- Câu ngắn, mỗi đoạn (paragraph) = 1 beat = 1 cảnh. Dấu câu rõ ràng để giọng đọc ngắt đúng.
- Câu nào trừu tượng thì phải có ẩn dụ hình ảnh cụ thể đi kèm (xem mục 3).
- Gửi kịch bản + bảng beat cho người dùng duyệt **trước khi** lồng tiếng (lồng tiếng tốn credit ElevenLabs).

## 2. Lời kể cụ thể → cảnh đúng nghĩa đen

| Lời kể | Cảnh |
|---|---|
| "Cô gái đang trên đường đi học" | Cô gái (đúng character_bible) đeo cặp đi trên con đường làng buổi sáng, máy `pan_left` theo bước chân |
| "Cô mở thư, bật khóc" | Cận tay cầm lá thư, rồi cận mặt rưng rưng; `push_in` |
| "Mười năm sau…" | Cùng địa điểm nhưng cảnh vật thay đổi, nhân vật lớn tuổi hơn (cập nhật bible, ghi rõ trong prompt) |

## 3. Đạo lý trừu tượng → ẩn dụ có hành động

Ẩn dụ phải: (a) có hành động thấy được, (b) có kết quả rõ ràng, (c) liên hệ hiển nhiên với lời kể.

| Chủ đề | Ẩn dụ (chuỗi cảnh) |
|---|---|
| Kiên trì, đừng bỏ cuộc khi đích đã gần | Hai người đào vàng. Người A đào sâu, chỉ còn một nhát là tới vỉ vàng thì vứt cuốc bỏ đi. Người B còn rất xa nhưng hì hục đào mỗi ngày, cuối cùng chạm vàng. Có thể dùng cảnh cắt ngang thấy lớp đất để khán giả *thấy* vàng chỉ cách A một gang tay. |
| Tích lũy nhỏ mỗi ngày | Giọt nước nhỏ đều lên tảng đá, qua thời gian đá lõm xuống / hạt mầm thành cây |
| Môi trường quyết định | Cùng một hạt giống: chậu đất khô vs vườn tốt |
| So sánh bản thân với người khác | Hai người leo hai ngọn núi khác nhau, một người cứ ngoái nhìn nên vấp ngã |
| Thời gian không quay lại | Đồng hồ cát, cát rơi; người chạy theo chuyến tàu vừa rời ga |
| Buông bỏ | Bàn tay mở ra thả con chim / thả hòn đá xuống nước |

Mỗi ẩn dụ chia thành 3–6 cảnh nối nhau theo nhân quả. Cảnh sau là kết quả của cảnh trước, không cắt ghép ngẫu nhiên.

## 4. Đồng nhất nhân vật và phong cách

- `style_bible.character_bible`: mỗi nhân vật 1 dòng cố định (giới tính, tuổi, tóc, trang phục, đặc điểm). **Dán nguyên văn** vào mọi prompt có nhân vật đó.
- `style_bible.visual_style`: hậu tố phong cách chung cho mọi prompt, ví dụ `"cinematic 3D Pixar-style animation, soft warm lighting, 9:16 vertical, high detail"` hoặc `"realistic cinematic photo, 35mm, golden hour, 9:16"`.
- Cùng địa điểm thì giữ mô tả bối cảnh giống nhau giữa các cảnh.

## 5. Prompt ảnh/video (ghi vào `build/prompts.md` và `assets[].prompt`)

Mẫu: `[chủ thể + character_bible] + [hành động cụ thể] + [bối cảnh] + [góc máy/khung hình] + [ánh sáng/cảm xúc] + [visual_style]`.

Ví dụ: `Two men digging for gold in a desert mine, cross-section view of the soil; man on the left (30s, red shirt, straw hat) throws down his pickaxe and walks away, a gold vein visible just 10cm below where he stopped; man on the right (30s, blue shirt) keeps digging far from the gold; wide shot, dusty golden light, sense of irony, cinematic 3D animation, 9:16 vertical`.

- Ảnh tĩnh: `render.py` tự thêm chuyển động máy (`push_in`, `pan_left`…) nên ảnh vẫn "sống".
- Video AI (Kling, Veo, Runway, Hailuo…): viết thêm hành động chuyển động trong prompt, đặt `kind: "video"`. Render tự cắt hoặc lặp cho khớp độ dài beat.
- Đặt tên file đúng `id` asset (`assets/s3.png`, `assets/s3.mp4`). Render sẽ tự nhận.

## 6. Chuyển động máy theo cảm xúc

| Cảm xúc / chức năng | motion |
|---|---|
| Hook, bước ngoặt, cao trào | `push_in` |
| Bối cảnh, mở rộng, kết luận | `pull_out` |
| Di chuyển, hành trình, thời gian trôi | `pan_left` / `pan_right` |
| Hy vọng, vươn lên | `pan_up` |
| Sụp đổ, thất vọng | `pan_down` |
| Lặng, suy ngẫm | `static` |

Các cảnh liền kề nên đổi hướng chuyển động để tránh nhàm.

## 7. Graphic động trong kể chuyện

- Chữ phải có hiệu ứng: phụ đề `story_pop` (từng từ hiện đúng lúc đọc), chữ chốt `kinetic_text` style `word_pop` (bật từng từ + phát sáng + gạch chân). Caption trên (`caption_top`) giống nhau mọi cảnh thì chỉ hiện MỘT lần ở đầu rồi đứng yên, không chạy lại mỗi cảnh.

- `kinetic_text` cho câu bài học/câu chốt ("ĐỪNG BỎ CUỘC", "CHỈ CÒN 1 NHÁT CUỐC").
- `counter` cho mốc thời gian/số lượng được nói ("365 ngày", "10 năm").
- `compare` cho đối lập hai nhân vật (Người bỏ cuộc vs Người kiên trì).
- Khoảng 1 graphic cho mỗi 3–5 beat. Đặt ở `top` hoặc `center` khi cảnh nền đủ tối/đơn giản.

## 8. Giọng đọc ElevenLabs

- Model `eleven_multilingual_v2` (ổn định cho tiếng Việt) hoặc `eleven_v3` (giàu cảm xúc hơn).
- Kể chuyện trầm ấm: stability 0.45–0.55, similarity 0.75, style 0.2–0.35, speed 0.95.
- Kịch tính hơn: stability 0.35, style 0.45.
- Ngắt nghỉ: xuống dòng giữa các đoạn và dùng dấu "…" hoặc "." để giọng tự ngắt.
- Chọn giọng: chạy `tts_elevenlabs.py --list-voices`, gửi 2–3 lựa chọn cho người dùng nghe thử bằng một câu ngắn trước khi đọc cả bài.
