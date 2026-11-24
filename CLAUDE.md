# Quy tắc dự án "quản lý edit video" (luôn áp dụng)

Xưng hô: người dùng là **anh**, Claude xưng **em**, trả lời tiếng Việt.

## Làm video → dùng skill, đúng quy trình
- Tạo / làm video theo nội dung → skill **tao-video**. Làm theo video mẫu (link/file) → **video-theo-mau**: CHỈ tham khảo và HIỂU DẠNG video/nhân vật/phong cách; KHÔNG đo từng khung hay sao chép nhịp, chuyển cảnh, chữ nhấn của mẫu — nội dung, kịch bản, edit, chuyển cảnh theo lời kể đều của skill mình (anh chốt 13/11/2026). Giọng kể ElevenLabs, sub từng từ, motion graphic, biểu đồ, khớp giọng–cảnh, chuyển cảnh, hậu kỳ CapCut → **ai-semantic-video-editor**. Ba skill phối hợp; đọc SKILL.md của skill trước khi làm.
- **Video kể chuyện phân tích kiến trúc / công trình** (kiểu "Chúc mừng bạn đã phát minh/xây thành công …", mô phỏng quá trình xây bằng 3D) → skill **video-mo-phong-quy-trinh** (anh chốt 11/11/2026): hình mô phỏng kỹ thuật 3D có chiều sâu (không quay thật), mở bằng bài toán gốc hoặc "xé toạc", đúng trình tự thi công, khuyết điểm → bạn giải, câu dẫn ngắn, kết chúc mừng + ảnh thật. Lệnh kiểm kịch bản: `prep.py`.
- Lời kể phải thú vị, vui nhộn vừa đủ ("người khôn như bạn…", "Thế là…", "bạn gọi nó là…", ví von, câu chốt): `ai-semantic-video-editor/references/giong-ke-hay.md` (anh yêu cầu 11/11/2026).
- Nguyên tắc nội dung: `ai-semantic-video-editor/references/content-quality.md` + `visual-mapping.md` (cảnh là video động diễn đúng từng câu thoại, không tạo cho có lệ, không bịa số liệu).

## LUẬT KHÔNG NGHỈ (anh yêu cầu 13/11/2026)
Mỗi giây em chạy đều tốn tiền của anh: KHÔNG dừng hỏi/chờ giữa các bước đã có trong quy trình; việc nào chờ (tool tạo cảnh) thì chạy nền và LÀM NGAY việc độc lập khác (giọng, SFX, ảnh thật, soát, xoá logo cảnh vừa về); chỉ một macro điều khiển giao diện tại một thời điểm, xếp nối đuôi. Việc trong quyền anh đã cấp (tool của anh, CapCut) làm luôn không xin lại; chỉ hỏi khi có thể xoá/đè dữ liệu của anh.
**Model tool: chỉ Omni 1.1 Flash, KHÔNG Omni 1.2 Flash** (đốt credit gấp ~3 lần). **CapCut: dùng cả chuyển cảnh Pro (anh cho phép, không chặn)**; riêng nút "Mua gói Pro để xuất video" thì không bấm mua, báo anh bật Pro rồi xuất.

## BẮT BUỘC: tạo qua Tool (AI VIDEO LIBRARY) thì dùng MACRO CHẠY NHANH
Không chạy macro nạp → chụp màn hình/zoom kiểm nút → chạy lệnh tạo nữa. Mỗi việc là MỘT lệnh, macro tự đọc nút bằng Windows OCR, số khớp mới bấm (từ thư mục dự án):

| Việc | Lệnh |
|---|---|
| Cảnh độc lập (Video AI, 1080p, xoá logo) | `python .claude/skills/ai-semantic-video-editor/scripts/auto_tool.py video projects/<slug>/storyboard.json --collect` |
| Cảnh nối tiếp (Studio Kịch Bản) — MỘT mạch, nhanh | `python .claude/skills/ai-semantic-video-editor/scripts/fast_tool.py projects/<slug>/storyboard.json --collect` (`auto_tool.py story …` cũ chậm hơn) |
| Ảnh AI (`image_jobs`) | `python .claude/skills/ai-semantic-video-editor/scripts/image_macro.py projects/<slug>/storyboard.json --auto --collect` |
| Giọng đọc TTS ElevenLabs (voice ID anh gửi, hoặc tự chọn) | `python .claude/skills/ai-semantic-video-editor/scripts/tts_macro.py projects/<slug>/storyboard.json --auto` |

- **Xóa hết prompt cũ trước khi nạp prompt dự án mới** (anh yêu cầu 09/11/2026) ở Studio Video AI / Studio Kịch Bản, để không còn dòng lạ bị tích. Lưu ý: "Xóa đã chọn" xóa luôn video đã tạo của các dòng đó khỏi thư viện tool, không khôi phục được → trước khi xóa kiểm tra video cũ đã có bản sao (`projects/<slug-cũ>/1-canh/` hoặc `D:\video`), dòng nào chưa có thì báo anh trước; không xóa dòng đang tạo.
- Lệnh có `--collect` chờ vài phút → chạy nền, làm việc khác trong lúc chờ.
- Chỉ xem ảnh trong `projects/<slug>/_macro/` khi macro in `STOP`; xử lý xong chạy lại (đã nạp prompt thì dùng `--only-generate`, không nạp lại để tránh trùng).
- An toàn tool: chỉ click / Ctrl+A / Ctrl+V / Esc; KHÔNG F12, Ctrl+Shift+I/J/C, Ctrl+U; không sửa file của tool; không đăng nhập, mua gói thay anh.

## BỘ NÃO ĐẠO DIỄN — áp cho MỌI video (anh duyệt 08/11/2026)
- Trước khi viết kịch bản: chẩn đoán thể loại, mục tiêu, khán giả, nền tảng, cách trình bày, cảm xúc, đường cảm xúc, độ nhạy cảm → `edit_profile` (xem `ai-semantic-video-editor/references/bo-nao-dao-dien.md`). Không có kiểu edit mặc định.
- Cách dẫn dắt, nhịp, nhấn mạnh từ khoá, chữ, sub, chuyển cảnh, SFX, nhạc, màu, hậu kỳ đều phải hợp hồ sơ: vui thì tếu và nảy, nghiêm trọng thì dứt khoát và nặng; đổi tông theo đoạn khi đường cảm xúc đổi.
- Mục tiêu cuối: video hay, có ý nghĩa, giữ người xem từ giây đầu (hook đúng thể loại, móc mới mỗi 5–8s, cao trào ~70–85%, kết đúng mục tiêu).
- **Tên riêng, chỉ đích danh, liệt kê, ý quan trọng → chữ nhấn có hiệu ứng + hình minh hoạ đúng loại** (anh yêu cầu 09/11/2026, chi tiết `ai-semantic-video-editor/references/bo-nao-dao-dien.md` mục 4b): phần mềm/app gọi tên → **logo chính thức**; danh xưng (tổ chức, người, địa danh, sự kiện) → **ảnh/video thật** có nguồn; liệt kê sự vật cụ thể (vd *bò, ngựa*) → **ảnh từng thứ** hiện đúng lúc đọc; liệt kê hành động/ý trừu tượng → **motion graphic** (tick, sơ đồ). Không phải chỗ nào cũng dùng icon. Lệnh: `callouts.py <sb> --stills …` rồi `callouts.py <sb>` trước khi xuất CapCut.
- Video tài liệu / review / giải thích / dữ liệu bằng motion graphic (bản đồ, hồ sơ, số liệu thật có nguồn) → skill **video-tai-lieu**.
  Lệnh (đọc `.claude/skills/video-tai-lieu/SKILL.md`, làm đủ 9 bước): `fetch_assets.py <sb>` → `pipeline.py projects/<slug> check` (sau MỖI lần sửa, chỉ đi tiếp khi in `OK`) → `pipeline.py … stills <giây…>` → `pipeline.py … render` (chạy nền) → `pipeline.py … capcut` (CapCut tắt) → `pipeline.py … review` (agent mới) → xuất CapCut → `pipeline.py … finish`. Giọng: `tts_macro.py <sb> --auto`. Thumbnail: `thumbnail.py <sb>`.
- **Kiểm cuối độc lập trước khi gửi anh** (anh duyệt 11/11/2026): `review_sheet.py projects/<slug>` rồi giao một agent mới soát theo `video-tai-lieu/references/kiem-cuoi.md`, chỉ gửi khi báo cáo `ĐẠT`. Tiêu đề lớn không treo (p.then). Chuyển động mới: breakout, dot_number, timeline, slider, orbit3d, exploded3d, flying_words, title thu nhãn, screen freeze (`modules.md`).
- **Graphic KHÔNG che dẫn chứng** (anh yêu cầu 11/11/2026, luật Q9 trong `video-tai-lieu/references/luat-dung.md`): ảnh / video / quay màn hình làm bằng chứng phải lộ trọn; chữ chốt đặt cột riêng cạnh bằng chứng, trên bằng chứng chỉ khoanh viền / đóng băng; `qa_layout.py` + `rule_check.py` tự chặn. Quay màn hình / video thao tác tool KHÔNG làm nền mờ dưới graphic: dùng module `screen` hiện rõ + cột chữ bên cạnh; nền mờ chỉ cho cảnh AI trang trí.
- **Graphic v2 là mặc định cho mọi video mới** (anh duyệt 10/11/2026): storyboard ghi `"design": "v2"` + `"brand_tag"`. Bản đồ giữ **ảnh vệ tinh bay từ vũ trụ** (anh thích hơn bản đồ vẽ) + lớp phủ viền phát sáng / tách đất / nhãn. Hook theo `video-tai-lieu/references/hook-thumbnail.md`; video YouTube luôn kèm thumbnail. Ảnh Ảnh AI dính logo Gemini → `gemini_wm.py` tự xử lý sau `image_macro.py --collect`.

## Dựng & xuất
- **Sub mặc định LUÔN là `story_pop`** (anh đã duyệt): cả cụm giữ chỗ sẵn, **mỗi từ hiện ra đúng lúc được đọc** (mờ vào + bật nhẹ), **từ đang đọc tô VÀNG** rồi chuyển trắng. Màu tô = màu nhấn `palette[2]` trong storyboard; mặc định vàng `#FACC15` — giữ tông vàng trừ khi anh yêu cầu màu khác. Chữ chốt `kinetic_text` (bật từng từ, phát sáng, gạch chân) và caption trên (hiện một lần rồi đứng yên) cũng dùng màu nhấn này.
- FFmpeg làm ĐẦY ĐỦ: `story_render.py` (cảnh khớp giọng, sub `story_pop`, chữ chốt, caption, chuyển cảnh mềm).
- **LUÔN hậu kỳ CapCut cho MỌI video** (anh yêu cầu): kiểm tra thật kỹ từng cảnh, rồi thêm hiệu ứng cảnh, hiệu ứng chuyển cảnh cho đẹp và sound effect cho mọi hành động phát tiếng, theo `references/capcut-post.md`. Không xuất thẳng bản FFmpeg; hiệu ứng hợp cảm xúc từng cảnh, đúng giây.
- **SFX khớp từng khung hình** (anh yêu cầu 09/11/2026): mỗi SFX có mốc bắt đầu VÀ kết thúc đo bằng `sfx_frames.py` (tắt đúng lúc hành động dừng, không lố sang cảnh khác, không sót đoạn có tiếng như cãi/quát/gõ/đi); sau mỗi lượt sửa trong CapCut chạy `capcut_sfx_check.py`, chỉ xuất khi in `OK`.
- Tự sửa cảnh lỗi (chữ lạ, nhòe, lệch nhân vật) trước khi dựng. Gửi anh duyệt video trong `2-xuat/`; chỉ dọn file tạm khi anh OK.
