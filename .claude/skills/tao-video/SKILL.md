---
name: tao-video
description: >-
  Làm video NHIỀU CẢNH QUAY bằng AI từ nội dung anh đưa: hoạt hình kể chuyện, người thật/KOC/thời trang, quảng cáo sản phẩm, mẹo/hướng dẫn, động vật, timelapse (vd "tạo video hoạt hình thỏ và rùa", "làm video KOC mặc áo hoodie này", "video quảng cáo bình giữ nhiệt 199K"). Viết kịch bản + prompt đồng nhất (kèm ảnh tham chiếu), tạo HÀNG LOẠT cảnh qua Tool AI VIDEO LIBRARY của anh (macro auto_tool.py) hoặc Web Muse, tải theo thứ tự, kiểm cảnh lỗi, giọng kể + vietsub, dựng và hậu kỳ CapCut rồi xuất. KHÔNG dùng cho video tài liệu / review phần mềm / số liệu / bản đồ dựng bằng motion graphic (→ video-tai-lieu); có link video mẫu → video-theo-mau trước.
---

# Tạo video tự động: Bắt đầu → Chọn chế độ → Nội dung → Kịch bản → Tạo cảnh (Web Muse / Tool) → Kiểm tra & cắt → Phụ đề → CapCut → Xuất

Anh chỉ cần nói nội dung (kèm ảnh người, sản phẩm nếu có). Claude làm **đạo diễn + biên tập + quản lý sản xuất** và tự chạy hết các bước. Chỉ dừng ở 4 điểm:
- 🛑 **Bắt đầu + chọn chế độ** (Bước 0).
- 🛑 **Duyệt kịch bản** (Bước 3), vì tạo video tốn hạn mức Muse / tool. Anh đã nói "làm luôn / tự động" thì bỏ qua.
- 🛑 **Tắt CapCut** trước khi script ghi project (Bước 7, 8).
- 🛑 **Duyệt video hoàn chỉnh** (Bước 10). Anh OK thì mới xoá clip cảnh con.

## Thư mục
```
projects/<slug>/                ← slug không dấu, gạch nối, vd tho-va-rua
  storyboard.json               ← kịch bản + bible chủ thể + prompt + lời thoại (nguồn sự thật)
  ref/                          ← ẢNH THAM CHIẾU anh đưa (người mẫu, sản phẩm, ảnh đầu/cuối)
  muse_jobs.json                ← chế độ Web: cảnh nào ở chat Muse nào, trạng thái
  tool_jobs.json                ← chế độ Tool: job nào của tool ứng với cảnh nào, đã lấy clip chưa (tool_jobs.py ghi)
  edit_plan.json                ← kế hoạch cắt (analyze_clips.py tạo)
  transcript.json               ← lời thoại nhận dạng được (transcribe.py tạo)
  1-canh/scene_01.mp4 …         ← VIDEO CẢNH (clip lẻ từ Muse)
  2-xuat/<Tên video>.mp4        ← VIDEO SAU KHI XUẤT (bản hoàn chỉnh)
```
`S=.claude/skills/tao-video/scripts`

## ⚡ TỐC ĐỘ (giữ nguyên quy trình Muse/Tool → CapCut, chỉ làm nhanh từng thao tác; mục 1 và 3 dành cho chế độ Web, chế độ Tool làm tương tự theo tool.md)
1. **Muse: gửi hết các cảnh trong 1 lượt.** Ref các nút giữ nguyên giữa các chat mới (nút + `Đoạn chat phụ mới`, ô đính kèm `input type=file`, ô `Nhắn tin`): `find` một lần rồi dùng lại. Mỗi cảnh = `[file_upload]` + 1 `browser_batch` (click ô → type → Enter → href → click + → wait 2 → find file input).
2. **Trong lúc Muse tạo video** (khoảng 2–3 phút cho cả lô): làm song song việc khác (kịch bản, dịch sub, cập nhật file). Không chụp màn hình để chờ, kiểm tra bằng JS.
3. **Thu hoạch:** mỗi chat = navigate → JS (toạ độ + kích thước video) → hover → 3 chấm → find "Tải xuống" → click → navigate chat kế tiếp, tất cả trong 1–2 batch. Tải cảnh nào `collect_clip.py` cảnh đó luôn. ẢNH thì tải ở trình xem lớn (bấm ảnh → nút Tải xuống).
4. **Đủ clip:** chạy song song `analyze_clips.py` + `transcribe.py` → dịch sub → `build_capcut_draft.py --replace` → `polish_draft.py`. Các lệnh này nối bằng `&&` trong 1 lệnh Bash.
5. **CapCut:** tự tắt khi không có cửa sổ (`taskkill //IM CapCut.exe`, cần thì `//F`), mở bằng `open_application`, mở project (ô đầu tiên ở trang chủ) → click vùng xem trước → `ctrl+e` → Xuất → chép sang `2-xuat`. Cả đoạn này gộp trong 1–2 `computer_batch`.
6. **Nhiều video cùng lúc:** mỗi video một phiên riêng (start_session) chạy song song. Agent phụ (Agent tool) lo kịch bản, dịch sub, kiểm tra clip trong lúc agent chính điều khiển trình duyệt và CapCut.
7. `wait` ngắn (1–3s), chụp màn hình `scale 0.5–0.6` chỉ khi cần nhìn.

---

## Bước 0 — Bắt đầu & chọn chế độ tạo cảnh (LUÔN làm đầu tiên)
1. Ngay khi skill được bật, gọi `AskUserQuestion` (header `Tạo video`):
   câu hỏi "Sẵn sàng tạo video chưa anh?" · lựa chọn **"Bắt đầu"** (mô tả: bắt đầu quy trình tạo video) và "Để sau".
   - "Để sau" → dừng, không làm gì thêm.
2. Anh bấm "Bắt đầu" → gọi tiếp `AskUserQuestion` (header `Chế độ`):
   câu hỏi "Anh muốn tạo video qua đâu?" · lựa chọn:
   - **"Qua Web Muse"**: điều khiển muse.ai trên Chrome (Claude in Chrome) → Bước 4A
   - **"Qua Tool của anh"**: điều khiển app AI VIDEO LIBRARY trên máy anh (computer use) → Bước 4B
3. Ghi chế độ vào `storyboard.json` (`"mode": "web"` hoặc `"mode": "tool"`) để chạy lại Bước 4 thì không phải hỏi lại.
4. Nếu anh đã nói sẵn trong tin nhắn ("làm qua web", "làm bằng tool", "làm luôn qua Muse"…) thì bỏ qua câu hỏi tương ứng. Skill **video-theo-mau** gọi sang cũng hỏi Bước 0 này trước Bước 4.
5. Chọn **Tool** mà [references/tool.md](references/tool.md) chưa ghi `ĐÃ HỌC` → lần chạy này làm chậm, chụp màn hình từng bước để đối chiếu, sửa tool.md cho đúng giao diện thật, xong thì đổi trạng thái (xem Bước 4B mục "Học tool").

Các bước 1–3 và 5–10 giống nhau cho cả hai chế độ. Chỉ Bước 4 khác.

## Bước 1 — Phân tích nội dung & chọn loại video
Tự chốt (mặc định trong ngoặc), chỉ hỏi khi nội dung thật sự mơ hồ:
- **Loại video** (`type`), quyết định cách viết prompt. Xem bảng trong [references/prompt-rules.md](references/prompt-rules.md):
  `animation` hoạt hình · `realistic` người thật/KOC/thời trang/vlog · `product` quảng cáo sản phẩm · `tips` mẹo/hướng dẫn/DIY · `nature` động vật/thiên nhiên · `review` review/tóm tắt · có thể trộn loại theo từng cảnh
- Mục tiêu: kể chuyện / bán hàng (có CTA, giá) / dạy mẹo / giải trí. Ai xem? (mặc định người Việt, chữ tiếng Việt)
- Tỉ lệ: (16:9), dùng 9:16 cho TikTok/Reels/Shorts/KOC/quảng cáo bán hàng
- Số cảnh: (6–8 × 10s cho kể chuyện, 3–5 cảnh cho quảng cáo/KOC). Anh nói thời lượng thì chia theo đó
- Phong cách: theo loại (hoạt hình 3D / người thật điện thoại / TVC studio / phim tài liệu…)
- **Ảnh anh gửi:** lưu vào `projects/<slug>/ref/`. Ảnh người hoặc sản phẩm là `reference_images`, ảnh trước/sau là `first_last`.

## Bước 1b — CHẨN ĐOÁN & HỒ SƠ EDIT (BẮT BUỘC, trước mọi kịch bản)
Đọc [../ai-semantic-video-editor/references/bo-nao-dao-dien.md](../ai-semantic-video-editor/references/bo-nao-dao-dien.md). Không có "kiểu edit mặc định":
- Trả lời 8 câu chẩn đoán (thể loại, mục tiêu, khán giả, nền tảng, cách trình bày, cảm xúc chủ đạo, đường cảm xúc, độ nhạy cảm) → ghi `"edit_profile"` vào storyboard.
- Kịch bản, lời thoại, nhịp, kiểu nhấn mạnh, chữ, sub, chuyển cảnh, SFX, nhạc, màu và hậu kỳ CapCut đều suy ra từ hồ sơ. Hoạt hình vui thì nhấn kiểu nảy/tếu/cartoon; vấn đề nghiêm trọng thì dứt khoát, nặng, không đùa; cảnh nào khác tông chung thì ghi `"mood"` riêng cho cảnh đó.
- Bảng duyệt kịch bản (Bước 3) PHẢI có dòng: **Hồ sơ edit: thể loại · mục tiêu · cảm xúc · nhịp · kiểu nhấn · sub · SFX**.
- Video dạng tài liệu / giải thích / dữ liệu / review bằng graphic (không cần cảnh AI) → dùng skill **video-tai-lieu**.

## Bước 2 — Bible chủ thể & bối cảnh (chìa khoá đồng nhất)
Đọc [references/prompt-rules.md](references/prompt-rules.md). Ghi vào storyboard:
- `type`, `style` (1 câu cố định)
- `subjects`: mỗi người / sản phẩm / con vật / nhân vật 1 câu cố định (có ảnh thì thêm "exactly as in the attached photo")
- `settings`: bối cảnh lặp lại. (tuỳ chọn) `lock` / `negative` riêng, không ghi thì script dùng mặc định theo `type`

## Bước 3 — Storyboard + prompt
1. Chép mẫu gần nhất trong `templates/` rồi sửa:
   - [tho-va-rua](templates/tho-va-rua.storyboard.json): hoạt hình kể chuyện 16:9
   - [koc-thoi-trang](templates/koc-thoi-trang.storyboard.json): người thật / KOC 9:16, ảnh tham chiếu, diễn biến theo giây
   - [quang-cao-san-pham](templates/quang-cao-san-pham.storyboard.json): sản phẩm 9:16, hero / macro / đang dùng, giá + CTA
   - [meo-huong-dan](templates/meo-huong-dan.storyboard.json): mẹo từng bước 16:9, timelapse trước/sau
2. Có lời kể (`narration`) → viết theo [../ai-semantic-video-editor/references/giong-ke-hay.md](../ai-semantic-video-editor/references/giong-ke-hay.md). Mỗi cảnh: `action` HOẶC `beats` (diễn biến theo giây), `camera`, `setting`, `subjects`, `subtitle` (chữ tiếng Việt ≤ 12 từ: chú thích / bước / giá / CTA), tuỳ chọn `dialogue`, `reference_images`, `first_last`, `continue_from_previous`, `keep`. Anh đưa prompt tự viết thì dùng `prompt_override`.
3. `python $S/make_prompts.py projects/<slug>/storyboard.json`
4. 🛑 Cho anh xem bảng `# | nội dung | chữ trên màn hình | ảnh đính kèm | nối tiếp?`.

## Bước 4A — Chế độ WEB: tạo HÀNG LOẠT trên Muse
Đọc [references/muse.md](references/muse.md): có toạ độ, cách gửi và cách tải đã kiểm tra thực tế.
- Chia thành chuỗi: cảnh không nối tiếp mở đầu chuỗi mới, cảnh `continue_from_previous` đi tiếp trong chuỗi trước. Vd 8 cảnh, cảnh 2 và 8 nối tiếp → [1,2] [3] [4] [5] [6] [7,8].
- **Gửi hết một lượt:** mỗi chuỗi bấm "+" một lần → (cảnh có ảnh: `file_upload` ảnh trong `ref/` trước, xem muse.md mục 1b) → gửi `[<Tên> - Cảnh N] <prompt>` → ghi `location.href` vào muse_jobs.json.
- **Thu hoạch theo thứ tự cảnh:** mở URL → JS kiểm tra video → tải bằng **menu 3 chấm → Tải xuống** (KHÔNG tải bằng JS) → `python $S/collect_clip.py projects/<slug>/1-canh N` → cảnh nối tiếp thì gửi tiếp trong cùng chat.

## Bước 4B — Chế độ TOOL: tạo HÀNG LOẠT bằng AI VIDEO LIBRARY

> **LIỀN MẠCH (13/11/2026):** Studio Kịch Bản dùng `fast_tool.py` (nạp prompt → gắn ảnh → bấm tạo trong một tiến trình, KHÔNG kiểm OCR chặn trước nút tạo, chờ ngắn ~10s tổng). Đo chỗ sững bằng `profile_macro.py`. Chi tiết: skill video-mo-phong-quy-trinh, mục "Luật liền mạch cho macro".

> **BẮT BUỘC — chạy nhanh bằng một lệnh:** KHÔNG làm "macro → Claude chụp màn hình/zoom kiểm nút → --only-generate" nữa. Dùng một lệnh của skill ai-semantic-video-editor: `auto_tool.py video|story <storyboard> --collect` (Video AI / Studio Kịch Bản) và `image_macro.py <storyboard> --auto --collect` (Ảnh AI), `tts_macro.py <storyboard> --auto` (giọng đọc TTS). Lệnh tự đọc nút bằng Windows OCR, số khớp mới bấm, không cần chụp màn hình; chỉ xem `_macro/` khi có STOP. Các bước tay bên dưới chỉ để hiểu / xử lý khi macro STOP.

**Chọn đúng chức năng của tool trước** theo bảng **⭐ BẢN ĐỒ CHỨC NĂNG** trong tool.md — chỉ dùng 3 studio: **Ảnh AI**, **Video AI**, **Studio Kịch Bản** (vd "video đồng nhất / nối frame cuối" → Studio Kịch Bản; cảnh độc lập → Video AI; cần ảnh nhân vật trước → Ảnh AI). Rồi đọc phần thao tác của chức năng đó, và **mục 0a bẫy chống crack** (không bấm F12 / Ctrl+Shift+I/J/C / Ctrl+U, không mở DevTools, không sửa file của tool — vi phạm là tool khoá máy vĩnh viễn).
- `request_access ["AI VIDEO LIBRARY"]` → `open_application "AI VIDEO LIBRARY"`. Điều khiển bằng `computer_batch`, chụp `scale 0.5–0.6` khi cần nhìn.
- ⚠️ **Model: chỉ Omni 1.1 Flash — KHÔNG Omni 1.2 Flash (đốt credit gấp ~3 lần, anh dặn 13/11/2026).** Tool thêm 1.2 lên đầu danh sách; macro `--model omni` đã chọn 1.1 nhưng PHẢI Read `_macro/1_canh1.jpg` kiểm ô model trước khi bấm tạo.
- Mặc định: nền tảng **Veo3 · Omni 1.1 Flash · 10s · 720p + Upscale tự động (→1080p) + Xóa watermark**, Tài khoản **Tự động**, tỉ lệ theo storyboard. Anh muốn Muse/Veo 3.1 Quality/Grok thì đổi theo lời anh.
- **Cảnh độc lập (đa số video) → MACRO, chạy liền một mạch ~40s, không chờ nhìn từng bước:**
  1. `python $S/tool_macro.py <storyboard> [--model omni] [--dur 10]` — app nổi trên cùng, tự nhập prompt, chọn tỉ lệ/model/thời lượng, bật Upscale + Xoá WM, áp cho các dòng mới, gắn ảnh tham chiếu từng cảnh. Mỗi bước tự kiểm tra trạng thái màn hình; in `STOP: …` là dừng an toàn → xem ảnh `_macro/STOP_*.jpg`, xử lý tay rồi chạy lại.
  2. Claude **zoom 1 lần** vùng (1330,14)-(1568,32): nút phải ghi đúng **"Tạo video N"** (N = số cảnh). Sai số → có dòng lạ đang tích → bỏ tích trước.
  3. `python $S/tool_macro.py <storyboard> --only-generate` → in "ĐÃ GỬI N/N cảnh".
  4. Lấy clip: `tool_jobs.py collect … --wait 900` (chạy nền).
- ⛔ Quy tắc bấm tay trên app: **(1553,23) vừa là X đóng ngăn chi tiết vừa là nút Tạo video** — chỉ bấm khi ảnh zoom MỚI NHẤT cho thấy ngăn đang mở. Bấm vào 1 dòng = app tự TÍCH dòng đó. Hộp Nhập prompt giữ nội dung cũ (Hủy không xoá).
- **Video đồng nhất / nối frame cuối / chuỗi liền mạch** → **Studio Kịch Bản** bằng MACRO (~20s):
  1. `python $S/tool_story_macro.py <storyboard> [--provider veo3|muse] [--model omni] [--dur 10]` — tạo dự án MỚI, chỉnh Cảnh 1, nạp danh sách prompt (mọi cảnh kế thừa cài đặt), gắn ảnh nhân vật vào Cảnh 1. In `STOP: …` là dừng an toàn → xem `_macro/STOP_*.jpg`.
  2. Claude zoom 1 lần (1440,72)-(1556,92): phải ghi **"TẠO VIDEO KỊCH BẢN N cảnh"**; xem nhanh các thẻ đúng nền tảng/tỉ lệ/thời lượng. Cảnh sau có ảnh riêng → gắn tay bằng nút (+) của thẻ đó.
  3. `python $S/tool_story_macro.py <storyboard> --only-generate` → `tool_jobs.py collect … --wait 1800` (chạy nền).
  4. Dựng CapCut: hoà tan ngắn ở mép nối (Studio Kịch Bản không khít từng pixel), cắt/che logo Gemini cuối clip (không có xoá WM, 720p).
- **Nhiều bối cảnh nhưng phải đồng nhất nhân vật** (vlog gia đình, KOC nhiều cảnh) → Ảnh AI tạo 1 ảnh nhân vật chuẩn → Ảnh AI tạo khung đầu từng cảnh (gắn ảnh chuẩn 1 lần + Áp dụng cho mục chọn) → `tool_macro.py --frames` (Video AI · Khung hình). Xem tool.md mục 2d–2e.
- **Cần ảnh nhân vật / sản phẩm / khung đầu trước** → **Ảnh AI** (tool.md mục 3a): tạo ảnh (Banana/ChatGPT Images/Muse/Grok, tỉ lệ + độ nét), rồi dùng ảnh đó làm tham chiếu cho Video AI hoặc Studio Kịch Bản.
- Trên thanh Studio Video: **Tự xóa = Tắt**, Tự động ghép = TẮT (mình dựng bằng CapCut).
- Lấy clip **không cần bấm tải, không cần chụp màn hình**: `python $S/tool_jobs.py collect <storyboard> --wait 900` (chạy nền) — đọc hàng đợi của tool, cảnh nào xong thì chép từ thư viện tool sang `1-canh/scene_XX.mp4`, ghi `tool_jobs.json`. Xem nhanh: `tool_jobs.py status <storyboard>`.
- Cảnh `Failed`: đọc mã lỗi (`AUTH_REQUIRED` → nhờ anh đăng nhập lại trong Browser Hub; `QUOTA_REACHED` → đổi tài khoản) → tạo lại cảnh đó trong tool (tối đa 2 lần, có thể đổi sang Muse AI).
- Trong lúc chờ: làm song song việc khác như chế độ Web.

### Học tool (lần chạy thật đầu tiên, hoặc khi tool đổi giao diện)
1. Làm theo tool.md, chụp màn hình sau mỗi bước, đối chiếu tên nút / vị trí. Lệch thì sửa tool.md ngay.
2. Ghi kích thước cửa sổ + vị trí tương đối các nút chính vào tool.md mục 0 (ưu tiên mô tả theo nhãn nút; toạ độ chỉ để tham khảo).
3. Chạy xong 1 video trọn vẹn → đổi dòng đầu tool.md thành `TRẠNG THÁI: ĐÃ HỌC <ngày>`. Từ lần sau chạy nhanh, gộp batch.
4. Không đăng nhập, không nhập key / mật khẩu, không mua gói trong License Center thay anh — gặp thì nhờ anh làm.

## Bước 5 — Tự kiểm tra & lập kế hoạch cắt
Chạy song song hai lệnh:
```
python $S/analyze_clips.py projects/<slug>/storyboard.json     # → edit_plan.json + 1-canh/_review.jpg
python $S/transcribe.py   projects/<slug>/storyboard.json     # → transcript.json
```
`analyze_clips.py` tự phát hiện:
- **Cảnh trùng** (gần như cùng hình ảnh với cảnh trước) → `drop`, bỏ khỏi video
- **Đứng hình** ở đầu/cuối → cắt bỏ. Đứng hình ở giữa clip → ghi chú để xem lại
- **Giật/nhảy hình** sát đầu/cuối → cắt bỏ. Nhảy hình ở giữa clip → ghi chú
- **Đoạn ì** (gần như không chuyển động) ở đầu/cuối > 1,5s → cắt bớt, giữ lại 1s. Không cắt ở mép nối với cảnh liền mạch
- Cảnh nối tiếp có khung đầu trùng khung cuối cảnh trước → cắt 0,2s cho đỡ khựng

Sau đó Claude **xem `_review.jpg`** (4 khung/cảnh) bằng mắt. Cảnh nào thiếu tự nhiên, lệch nhân vật, hỏng hình:
- sửa được bằng cắt → chỉnh `trim_start` / `trim_end` trong edit_plan.json
- không cứu được → `drop: true`, hoặc làm lại cảnh đó trên Muse / tool (tối đa 2 lần)

## Bước 6 — Phụ đề (tự chọn theo nội dung)
- **Có thoại** (`transcript.json` có câu): Claude dịch sang tiếng Việt tự nhiên, ngắn gọn. Bỏ tiếng ậm ừ, ngáp, "hmm". Tiếng cười có thể giữ là "Ha ha ha!". Ghi vào `scenes[i].lines = [{"start","end","text"}]`, giữ nguyên mốc giây của transcript. → **vietsub chạy đúng lúc nhân vật nói**.
- **Không thoại** (cảnh rỗng trong transcript): dùng `subtitle` làm **chú thích cốt truyện** suốt cảnh, để người xem hiểu truyện.
- Video `review` thì mọi câu thoại đều vietsub. Không thêm giọng AI.

### (Tuỳ chọn) Giọng kể ElevenLabs thay cho giọng đọc trong clip
⚠️ **Chỉ dùng ElevenLabs khi video CẦN tiếng người** (có lời kể / thoại, hoặc anh yêu cầu giọng) — anh chốt 26/11/2026. Video không lời (động vật AI, hài tình huống chỉ nhạc, timelapse, video mẫu không có giọng) → không tạo giọng, không sub, chỉ cảnh + nhạc (+ SFX).
Video kể chuyện, đạo lý hay giải thích cần **một giọng đọc đồng nhất xuyên suốt**: dùng skill **ai-semantic-video-editor**, mục "Dùng chung với skill tao-video". Tóm tắt: lời kể ghi vào `narration` (không ghi vào `dialogue`) → `tts_macro.py` tạo giọng ở mục **Giọng đọc (TTS)** của tool và đồng bộ (~25s) → sau Bước 7 chạy `capcut_narration.py` (cảnh, sub, graphic khớp theo giọng) → Bước 8 và 9 như cũ.

## Bước 7 — Dựng CapCut (script)
🛑 Kiểm tra CapCut đã tắt (`tasklist | grep -ci capcut` phải ra 0). Nếu Claude là người mở CapCut thì tự đóng: nút X góc phải trên (1560, 8) bấm 2 lần.
```
python $S/build_capcut_draft.py projects/<slug>/storyboard.json --replace
```
- Đọc edit_plan: bỏ cảnh `drop`, cắt đầu/cuối theo `trim_*`
- Cảnh có `"keep": [a, b]` thì chỉ lấy đoạn từ giây a đến giây b của clip. Dùng cho nhịp cắt nhanh, và nhiều cảnh có thể dùng chung 1 clip với các `keep` khác nhau (skill video-theo-mau dùng cách này)
- Vietsub theo `lines`, chú thích theo `subtitle`
- Chuyển cảnh giữa các cảnh khác nhau. Chỗ cảnh nối liền mạch thì cắt thẳng, không chuyển cảnh
- `--replace`: thay project cũ cùng tên. Chỉ thay project do skill tạo (có file `.tao_boi_skill_video_hoat_hinh`), không bao giờ đụng project của anh

## Bước 8 — Làm đẹp (script, dùng kiểu dáng đã học từ giao diện CapCut)
```
python $S/polish_draft.py "<Tên video>"
```
Script áp cho tất cả dòng chữ: chữ trắng viền đen, đổ bóng, hiệu ứng chữ hiện vào. Thêm bộ lọc màu "Rực sáng" 60% cho cả video. Kiểu dáng lấy từ [assets/capcut_style_pack.json](assets/capcut_style_pack.json).
Muốn đổi kiểu (chữ vàng, hiệu ứng khác, bộ lọc khác): làm **một lần** trên giao diện CapCut cho 1 dòng chữ hoặc 1 bộ lọc, đóng project, đọc JSON rồi cập nhật style pack. Cách làm có trong [references/capcut-ui.md](references/capcut-ui.md).

## Bước 9 — Xuất video (giao diện CapCut)
Theo [references/capcut-ui.md](references/capcut-ui.md): mở CapCut → mở project → `ctrl+e` → 1080p, 30fps → Xuất (lưu mặc định vào `%LOCALAPPDATA%\CapCut\Videos`) → chờ xong → chép sang `projects/<slug>/2-xuat/` → ffprobe + `_check.jpg` 4 khung để kiểm tra.
⚠️ Nếu CapCut báo "Bạn đang sử dụng các tính năng Pro": KHÔNG bấm Mua hay Dùng thử. Bấm "Quay lại phần chỉnh sửa", báo anh bật Pro, hoặc đổi sang hiệu ứng miễn phí.

## Bước 10 — Duyệt & dọn dẹp
1. 🛑 Gửi anh video trong `2-xuat` (SendUserFile) kèm tóm tắt: thời lượng, cảnh nào đã cắt/bỏ và vì sao.
2. Anh sửa gì → chỉnh storyboard / edit_plan → chạy lại Bước 7–9.
3. **Anh OK** → xoá `1-canh/*.mp4`, `_review.jpg`, các bản Muse / tool còn sót trong Downloads (hoặc thư mục tool lưu) của video này, và project nháp CapCut của video đó nếu anh muốn. Chỉ xoá khi anh đã nói OK trong chat.

---

## Chia việc (video dài > 8 cảnh)
Claude chính giữ storyboard + muse_jobs + edit_plan và là agent duy nhất điều khiển Chrome, tool của anh và CapCut. Có thể giao subagent:
- **Biên kịch:** viết/duyệt `action`, đối chiếu bible
- **Biên tập:** đọc `_review.jpg` + edit_plan, đề xuất cắt/bỏ
- **Dịch sub:** dịch transcript.json sang `lines` tiếng Việt
Những việc này không đụng giao diện nên chạy song song được.

## Quy tắc an toàn
- Không đăng nhập, không mua gói hay dùng thử Pro thay anh. Gặp màn hình tài khoản hoặc thanh toán → nhờ anh.
- Muse báo "video generation isn't available … region" → báo anh đổi tài khoản.
- Không xoá chat Muse, không sửa project CapCut của anh (chỉ project có file đánh dấu của skill).
- Xoá clip cảnh con chỉ sau khi anh duyệt video hoàn chỉnh.
