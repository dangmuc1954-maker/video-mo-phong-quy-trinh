---
name: video-theo-mau
description: >-
  Làm video MỚI "theo dạng" một video mẫu anh gửi (link TikTok, YouTube/Shorts, Facebook/Reels, Instagram, Douyin… hoặc file có sẵn). Claude tải video mẫu, XEM và HIỂU nó thuộc dạng gì (thể loại, kiểu nhân vật, phong cách hình, cách trình bày, chất cảm xúc, cách kể), rồi tạo một video cùng dạng nhưng nội dung, kịch bản, lời kể, edit, chuyển cảnh, âm thanh, hậu kỳ hoàn toàn của riêng skill mình (không đo từng khung / từng giây, không sao chép nhịp hay hiệu ứng của mẫu). Dùng khi anh gửi link/file video và bảo "làm video giống vậy", "tạo video kiểu này", "làm theo mẫu này", "nhân vật dạng này". Sản xuất theo dạng mẫu: tài liệu/graphic/số liệu → video-tai-lieu; mô phỏng quy trình/kiến trúc → video-mo-phong-quy-trinh; ảnh tĩnh người que/bút chì kể đạo lý → xem bảng Bước 4; hoạt hình/KOC/quảng cáo cảnh AI → tao-video. Không có video mẫu thì KHÔNG dùng skill này.
---

# Video theo mẫu: Xem mẫu → HIỂU DẠNG → làm nội dung & edit của riêng mình

## NGUYÊN TẮC GỐC (anh chốt 13/11/2026)
Video mẫu chỉ để **tham khảo và hiểu DẠNG video**. Mọi thứ còn lại là của skill mình.

| Lấy từ mẫu (ở mức hiểu dạng) | KHÔNG làm — cấm máy móc |
|---|---|
| Thể loại (đạo lý, review, mẹo, tài liệu, hài…) và đối tượng người xem | Đo từng khung hình / từng giây / độ chênh khung, lập bảng theo giây |
| **Dạng nhân vật** (vd "người que đầu tròn trắng không mặt", "bé hoạt hình 3D", "KOC thật") — để tạo nhân vật CÙNG DẠNG nhưng của mình | Chép nhịp cắt, độ dài từng cảnh, kiểu và độ dài chuyển cảnh, mức zoom, thời điểm chữ nhấn của mẫu |
| Phong cách hình tổng thể (bút chì đen trắng, 3D, ảnh thật…) và cách trình bày chung (tiêu đề trên, dải ảnh giữa, sub dưới…) | Dùng lại lời thoại, cốt truyện, chủ đề cụ thể, nhân vật có bản quyền, logo, watermark, mặt người thật |
| Chất cảm xúc và kiểu kể (hỏi thẳng người xem, ngôi thứ hai, ẩn dụ…) | Đặt chuyển cảnh / SFX / nhạc / chữ nhấn theo mẫu |

### SÁT KIỂU MẪU + GIỌNG CHỈ KHI CẦN (anh chốt 26/11/2026)
- **Video làm ra phải SÁT KIỂU mẫu**: người xem nhìn là thấy "cùng một kiểu video". Giữ đúng: dạng nhân vật, chất hình (ảnh thật kiểu phim / 3D / vẽ…), tỉ lệ khung, độ dài tổng gần mẫu, kiểu âm thanh (chỉ nhạc / nhạc + tiếng động / có giọng kể), có hay không có chữ trên màn hình, kiểu mạch truyện (vd chuỗi tình huống hài của cùng nhóm nhân vật). Cái mới là tình huống, câu chuyện cụ thể — không chép từng cảnh của mẫu.
- **Xem mẫu KỸ trước khi viết** (bài học 26/11: bản đầu "mèo giang hồ" bị chê "chưa phải phim hành động, không tự nhiên"): trích tấm 1 khung/giây của CẢ video mẫu (`ffmpeg -vf fps=1,scale=320:-1,tile=8x3`) và xem hết, ghi vào `phan_tich.md`:
  1. **Mức hành động / thể loại phim** (phim hành động rượt đuổi? đời thường? hài tĩnh?) — prompt `style` phải nói đúng thể loại phim, vd "gritty Asian crime action movie, handheld, motion blur, NOT glossy, NOT posed".
  2. **Ngôn ngữ máy quay**: cầm tay / sát đất / lướt theo / tiền cảnh che / rack focus / whip pan — ghi vào `camera` từng cảnh.
  3. **Nhân vật diễn thế nào**: động vật đi lại như thật hay tạo dáng; người thật phản ứng ra sao. Mỗi cảnh phải có HÀNH ĐỘNG + PHẢN ỨNG (dùng `beats` theo giây), không cảnh "ngồi nhìn".
  4. **Các loại tình huống** trong mạch (cướp → rượt → đàn em chào → đột kích → giao dịch → hưởng thụ → tiệc → dằn mặt → bước ra) — làm đủ các loại tình huống đó bằng chi tiết của mình (bối cảnh Việt, đồ vật khác).
  5. Dựng: cắt trên chuyển động, chuyển cảnh nhòe lướt, màu phim thống nhất; nhạc đúng thể loại (hành động → trống/bass căng, có cao trào).
- **ElevenLabs CHỈ dùng khi video cần tiếng người**: mẫu có giọng kể / thoại người, hoặc anh yêu cầu giọng. Mẫu chỉ có nhạc / tiếng động (vd video AI động vật, timelapse, hài không lời) → KHÔNG tạo giọng, KHÔNG sub story_pop, KHÔNG chữ nhấn; chỉ cảnh + nhạc nền (+ SFX nếu mẫu có), giữ đúng chất "không lời" của mẫu. Ghi `"voice": "none"` trong storyboard.
- Anh nói "không cần hậu kỳ CapCut" → dựng và xuất thẳng bằng FFmpeg (ghép cảnh, chuyển cảnh mềm, nhạc), vẫn tự kiểm cảnh lỗi trước khi gửi.

**Nội dung và edit là của skill mình:** chủ đề mới, kịch bản mới, lời kể mới (theo `giong-ke-hay.md`), hồ sơ edit (`bo-nao-dao-dien.md` → `edit_profile`), nhịp cắt / chuyển cảnh / chữ nhấn / SFX / nhạc / hậu kỳ CapCut quyết định theo LỜI KỂ và cảm xúc của video MỚI, đúng quy tắc của skill sản xuất tương ứng. Giống mẫu ở "trông cùng một dạng video", khác ở "mọi chi tiết bên trong".

```
projects/<slug>/
  0-mau/            ← video mẫu + ghi chú hiểu dạng (video.mp4, keyframes.jpg, phan_tich.md ngắn)
  storyboard.json   ← kịch bản video mới (của mình)
  1-canh/  2-xuat/  ← như skill sản xuất tương ứng
```
`T=.claude/skills/video-theo-mau/scripts`

---

## Bước 1 — Tải mẫu và XEM (khoảng 10–30s)
```
python $T/analyze_reference.py "<link hoặc đường dẫn file>" projects/<slug>
```
- Tải video, trích vài khung đại diện (`keyframes.jpg`), nhận dạng lời thoại (`transcript`). **Dùng để XEM và ĐỌC cho hiểu**, bỏ qua các con số nhịp cắt / số cảnh / giây-mỗi-cảnh script in ra.
- Xem `keyframes.jpg` (Read) + đọc hết lời thoại. Cần xem thêm thì trích vài khung bằng ffmpeg, vài khung là đủ, không quét từng khung.
- **Tải không được** (riêng tư / cần đăng nhập): hỏi anh cho dùng cookie trình duyệt (`--cookies-from chrome`), hoặc mở link bằng Claude in Chrome xem và chụp vài mốc, hoặc nhờ anh tải file về.

## Bước 2 — HIỂU DẠNG (Claude tự làm, ghi ≤ 15 dòng vào `0-mau/phan_tich.md`)
Không có bảng theo giây, không có số đo. Viết bằng lời, ngắn:

| Mục | Ghi gì |
|---|---|
| Dạng video | thể loại, nền tảng thường đăng, tỉ lệ khung, đối tượng người xem |
| Chủ đề & mạch | video kể chuyện gì từ đầu tới cuối (1–2 câu), thông điệp đọng lại |
| **Dạng nhân vật** | nhân vật thuộc dạng nào, đặc điểm nhận dạng chung (vd đầu tròn trắng, hai chấm mắt, áo thun) — để tạo nhân vật cùng dạng |
| Phong cách hình | chất liệu / màu / ánh sáng / cách bố cục khung (tiêu đề, dải ảnh, sub nằm ở đâu — mức tổng quát) |
| Chất giọng & cảm xúc | giọng kể thế nào, cảm xúc chủ đạo và đường cảm xúc |
| Vì sao cuốn | 3–5 ý (không phải số giây) |

Cho anh xem tóm tắt 4–6 dòng, nêu 1 câu "đây là dạng video gì". Nếu anh sửa "em hiểu sai dạng" thì sửa ngay rồi đi tiếp.

## Bước 2b — CHỌN CÁCH SẢN XUẤT THEO DẠNG, rồi chẩn đoán & hồ sơ edit (BẮT BUỘC)
Chạy bộ não [../ai-semantic-video-editor/references/bo-nao-dao-dien.md](../ai-semantic-video-editor/references/bo-nao-dao-dien.md) cho video MỚI → `edit_profile`. Chuyển cảnh, nhịp, chữ nhấn, SFX, nhạc, hậu kỳ lấy từ hồ sơ này và từ lời kể mới, không lấy từ mẫu (xem mục "Chuyển cảnh theo lời kể" trong bo-nao-dao-dien.md).

## Bước 3 — Nội dung & kịch bản MỚI (của mình)
- **Anh có đưa nội dung** → dùng đúng nội dung đó.
- **Anh không đưa** → Claude tự nghĩ chủ đề / câu chuyện **mới**, hữu ích, có ý nghĩa, cùng dạng và đối tượng với mẫu. Ghi 1 câu logline trong bảng duyệt.
- Viết lời kể theo [../ai-semantic-video-editor/references/giong-ke-hay.md](../ai-semantic-video-editor/references/giong-ke-hay.md) và [../ai-semantic-video-editor/references/content-quality.md](../ai-semantic-video-editor/references/content-quality.md). Số cảnh và độ dài từng cảnh theo **lời kể mới** (một câu / một ý ≈ một cảnh), không theo số cảnh của mẫu.
- **MỘT MẠCH, không phải N khoảnh khắc rời:** chốt logline trước; cảnh đầu nêu vấn đề, cảnh giữa leo thang, cảnh cuối là điểm rơi (twist, giải quyết, câu chốt đọng lại).
- **Nhân vật cùng DẠNG, không phải nhân vật của mẫu:** mô tả lại bằng lời mình (đặc điểm nhận dạng chung), copy nguyên văn mô tả đó ở mọi cảnh. Người thật / KOC: xin ảnh người mẫu của anh làm `reference_images`, không dùng mặt trong mẫu.
- Tỉ lệ khung theo nền tảng đăng (TikTok/Reels/Shorts 9:16, YouTube 16:9).
- 🛑 Bảng duyệt: `logline` + `# | lời kể | hình | chữ nhấn` (anh nói "làm luôn" thì bỏ qua).

## Bước 4 — Sản xuất: chọn skill theo DẠNG của mẫu
| Dạng mẫu | Sản xuất bằng |
|---|---|
| Tài liệu / review / giải thích bằng graphic, số liệu, bản đồ | skill **video-tai-lieu** |
| Mô phỏng quy trình xây dựng / kiến trúc ("Chúc mừng bạn đã phát minh/xây…") | skill **video-mo-phong-quy-trinh** |
| Đạo lý / kể chuyện bằng **ảnh tĩnh** (người que, bút chì, tranh vẽ) + giọng kể + zoom chậm | Ảnh AI hàng loạt (`image_jobs` + `image_macro.py`) → giọng (`tts_parts.py`) → `strip_clips.py` (ảnh → clip dải giữa) → `story_render.py` → `post_capcut.py` (skill video-mo-phong-quy-trinh có các script này) |
| Hoạt hình / người thật / KOC / quảng cáo cảnh AI | skill **tao-video** (Studio Kịch Bản / Video AI / Muse) |

Luật chạy chung: không dừng chờ, việc chờ thì làm việc khác (xem CLAUDE.md "Luật không nghỉ"); macro liền mạch (`fast_tool.py`); model tool chỉ Omni 1.1 Flash; hậu kỳ CapCut đầy đủ (chuyển cảnh theo lời kể, SFX mọi hành động, nhạc); AI soát độc lập trước khi gửi anh.
Khi gửi anh duyệt: 2–3 dòng "giống mẫu ở đâu (dạng), khác ở đâu (nội dung, edit)". Anh duyệt xong: xoá `0-mau/video.mp4`, giữ `phan_tich.md`.

## Làm nhiều video từ 1 mẫu
"Làm 3 video như vậy": dùng chung `phan_tich.md` (dạng), mỗi video một slug và một chủ đề khác nhau, chạy song song những việc độc lập.
