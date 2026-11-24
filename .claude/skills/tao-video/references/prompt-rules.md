# Viết prompt Muse cho mọi loại video

`make_prompts.py` ghép prompt theo khung chung:
```
[Use the attached image(s) as the exact visual reference.]      ← có reference_images
[Image 1 is the exact first frame, image 2 the exact last frame.] ← có first_last
[Continue seamlessly from the last frame of the previous video.]  ← continue_from_previous
Create a 10-second video, <aspect> <orientation>, single continuous shot.
Style: <style>.
Subjects: NAME = <mô tả cố định> …
Setting: <bối cảnh>.
Action: <1 hành động>   HOẶC   Action timeline: 0–2s: … 2–5s: … 5–10s: …
Camera: <góc máy, chuyển động>.
[Dialogue (spoken aloud, clear voice): …]
Consistency: <câu khoá đồng nhất>
Negative: <câu cấm>
```
Anh có prompt tự viết sẵn thì dùng `prompt_override` cho cảnh đó, script giữ nguyên.

## Quy tắc chung (mọi loại)
1. **Đồng nhất tuyệt đối, không phải "tương tự":** mỗi chủ thể có 1 câu mô tả cố định, COPY NGUYÊN VĂN (không diễn đạt lại, không đổi 1 chữ) ở mọi cảnh có mặt chủ thể đó. Có ảnh thì đính kèm ảnh vẫn tốt hơn mô tả bằng chữ.
   - Video có người/nhân vật xuất hiện ở ≥2 cảnh (vlog, KOC nhiều cảnh, hoạt hình nhiều bối cảnh): **mặc định mọi cảnh phải khoá đồng nhất với nhau**, không được để cảnh nào "tự do". Chọn một trong hai, không trộn nửa vời:
     - **Nối khung hình liên tục** (`continue_from_previous: true` ở MỌI cảnh 2+, tool thì dùng Studio Kịch Bản/Chuỗi Kịch Bản) — mạnh nhất, cảnh sau luôn bắt đầu đúng từ cảnh trước.
     - **Cùng 1 ảnh tham chiếu** gắn vào `reference_images` của **MỌI cảnh không trừ cảnh nào** (không phải chỉ cảnh đầu).
   - Đừng để video có cảnh đồng nhất tốt rồi tới cảnh không gắn gì cả — một cảnh lệch là cả video mất đồng nhất.
2. **Một cảnh 10s = một hành động chính.** Cần nhiều động tác thì dùng `beats` chia theo giây (Muse làm theo mốc giây tốt).
3. **Camera rõ ràng:** wide / medium / close-up / macro; static / push-in / pull-back / pan / tracking / orbit / handheld. Không cắt cảnh trong 1 clip.
4. **Không có chữ trong video.** Chữ, giá, tiêu đề làm ở CapCut.
5. Tỉ lệ ghi trong prompt khớp `aspect` của storyboard.
6. **Khớp NĂNG LƯỢNG của video mẫu/yêu cầu**, đừng mặc định "ấm áp, êm dịu" cho mọi video. Nội dung vui/hài/năng động → style phải nói rõ "energetic, punchy, bright vibrant colors, upbeat pacing", camera có chuyển động (không toàn static), biểu cảm nhân vật phóng đại hơn bình thường (giật mình, cười to, mắt tròn). Nội dung sâu lắng/tình cảm mới dùng "soft warm, gentle" — không áp cho video đáng lẽ phải vui nhộn.

## Viết lời thoại HAY và NHẤT QUÁN — lỗi hay gặp nhất
Thoại nhạt, nghe như liệt kê chứ không như trò chuyện thật là lỗi hay gặp nhất. Trước khi điền `dialogue`, kiểm tra từng câu:
1. **Một "chất giọng" xuyên suốt, không đổi tính cách giữa các cảnh.** Chốt trước 1 câu mô tả tính cách mỗi nhân vật (vd "bé lí lắc, hay cãi lại nhưng dễ xiêu lòng"; "mẹ hay trêu, giọng tỉnh bơ") rồi viết thoại đúng tính cách đó ở MỌI cảnh — không để cảnh 1 bé nhõng nhẽo, cảnh 3 bé nói như người lớn.
2. **Mỗi câu thoại là một "miếng" hài (bit), không phải câu mô tả hành động.** Có mồi (setup) + điểm rơi (punchline) bất ngờ hoặc ngược mong đợi. "Con ăn cơm đây" là câu mô tả (nhạt). "Con ăn hết rồi… của con chó luôn đó mẹ!" là một miếng hài (có twist).
3. **Thoại phải ĐỐI ĐÁP, không phải 2 câu độc thoại cạnh nhau.** Câu sau phản ứng trực tiếp với câu trước (ngạc nhiên, cãi lại, đồng tình kiểu trớ trêu...), giống hội thoại thật.
4. **Lặp lại một "câu cửa miệng" (catchphrase) hoặc một kiểu chốt câu xuyên suốt video**, giống video mẫu hay lặp một dòng chữ/thoại ở nhiều cảnh (vd "POV: …" lặp 3 lần) — chọn 1 câu/mô-típ của riêng video mình, dùng lại ở 2+ cảnh để tạo điểm nhấn ghi nhớ, KHÔNG sao chép nguyên câu của video mẫu.
5. Trước khi chốt kịch bản, tự đọc to 2 lượt thoại: nếu đọc lên thấy "ổn nhưng không buồn cười" → viết lại, đẩy twist mạnh hơn hoặc phản ứng cường điệu hơn.

## Theo loại video (`"type"`)

### animation: hoạt hình, kể chuyện
- style: "3D Pixar-like cartoon / 2D hand-drawn / anime / clay stop-motion…"
- Nhân vật có 1–2 phụ kiện nhận diện (khăn đỏ, kính tròn).
- Cần thoại thì dùng `dialogue` tiếng Anh ngắn, sau đó vietsub.

### realistic: người thật, KOC, thời trang, vlog, POV
- **Luôn dùng ảnh tham chiếu** của người hoặc trang phục (`reference_images`). Không có ảnh thì mô tả rất chi tiết: tuổi, tóc, khuôn mặt, trang phục, màu.
- style: "ultra-realistic smartphone fashion video, natural daylight" / "cinematic 35mm, shallow depth of field" / "UGC TikTok style, handheld".
- Động tác chia `beats` theo giây, mô tả cả tay và vải (kéo khoá, chỉnh mũ, xoay người).
- Consistency mặc định: giữ nguyên mặt, tóc, dáng, trang phục, logo, ánh sáng, nền. Tay và ngón tay đúng, vải chuyển động tự nhiên.
- Negative mặc định: không biến dạng mặt, không thừa ngón tay, không đổi trang phục, không rung máy.
- Muốn cảnh kết thúc đúng một tư thế thì dùng `first_last` (chế độ khung hình của Muse).

### product: quảng cáo sản phẩm, TVC, unbox
- Ảnh sản phẩm thật làm `reference_images` ở MỌI cảnh có sản phẩm.
- Cảnh hay dùng: hero shot xoay 360°, macro chi tiết chất liệu, đang dùng (in-use), trước/sau, đặt trong bối cảnh sống.
- style: "premium commercial product video, studio lighting, clean background" / "lifestyle ad, warm natural light".
- Tên sản phẩm, giá, CTA ghi ở CapCut (`subtitle`), không ghi trong prompt.

### tips: mẹo, hướng dẫn, xây dựng, nấu ăn, DIY
- Mỗi cảnh = 1 bước. `subtitle` = "Bước 1: …".
- Camera: top-down hoặc over-the-shoulder, cận tay đang làm.
- Timelapse (dọn đất, xây nhà, nấu ăn) thì dùng `first_last` với ảnh trước và ảnh sau, kèm "timelapse".

### nature: động vật, thiên nhiên, nông trại
- Mô tả con vật (giống, màu lông, đặc điểm) cố định qua các cảnh. Có âm thanh tự nhiên thì ghi "natural ambient sound, the cow moos".
- style: "documentary 4K, natural light" hoặc hoạt hình tuỳ yêu cầu.

### review: tóm tắt, review, kể chuyện có người dẫn
- Nhân vật dẫn chuyện cố định + `dialogue`. Phụ đề làm vietsub toàn bộ.

## Lỗi hay gặp → nhắn lại Muse trong cùng chat
| Lỗi | Nhắn lại |
|---|---|
| Lệch mặt hoặc trang phục so với ảnh | "Redo: match the attached reference exactly: same face, same outfit, same colors." |
| Sản phẩm méo, sai logo | "Redo: the product must look exactly like the attached photo, label readable, no distortion." |
| Thừa ngón tay, tay lỗi | "Redo with natural hands, five fingers, no extra limbs." |
| Có chữ hoặc logo lạ | "Redo without any text, letters or watermark." |
| Sai tỉ lệ | "Redo in 9:16 vertical (or 16:9 landscape), 10 seconds." |
| Kết thúc thả lỏng, sai tư thế cuối | Dùng `first_last` hoặc "hold the final pose for the last 2 seconds." |
