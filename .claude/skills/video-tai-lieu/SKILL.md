---
name: video-tai-lieu
description: >-
  Làm video TÀI LIỆU / REVIEW / GIẢI THÍCH / DỮ LIỆU / MARKETING PHẦN MỀM bằng motion graphic dựng bằng code (HTML → MP4), có ảnh/video/quay màn hình THẬT làm dẫn chứng, giọng kể ElevenLabs, sub story_pop vàng, hậu kỳ CapCut tự động (SFX + nhạc). Dùng khi anh nói: "làm video tài liệu", "review sản phẩm / dự án / tool / app kiểu graphic", "video giới thiệu phần mềm", "giải thích số liệu", "kể vụ án / lịch sử / tiểu sử", "tin tức", "video có bản đồ / biểu đồ / số liệu", "edit kiểu video tài liệu này", hoặc video mẫu (video-theo-mau) là dạng graphic tài liệu. KHÔNG dùng cho video kể chuyện hoạt hình / KOC / quảng cáo cảnh AI thuần (→ tao-video), làm theo link mẫu (→ video-theo-mau trước).
---

# Video tài liệu bằng motion graphic

Đọc file này TỪ ĐẦU ĐẾN CUỐI trước khi làm. Làm đúng thứ tự 9 bước; mỗi bước có **cổng qua**: chưa thấy dòng `OK` thì không đi tiếp.

```
V=.claude/skills/video-tai-lieu/scripts      A=.claude/skills/ai-semantic-video-editor/scripts
projects/<slug>/ storyboard.json · facts.json · narration/ (voice.mp3, words.json, sync.json) · assets/ · render/ · 2-xuat/
```

Chạy từ thư mục dự án gốc (`D:\dự án antigravity\quản lý edit video`). Trên Windows luôn đặt `export PYTHONIOENCODING=utf-8` trước lệnh python (tránh lỗi `charmap` khi in tiếng Việt). Lệnh lâu (render) → `run_in_background`.

## LUẬT VÀNG (anh đã duyệt — vi phạm là làm lại)

| # | Luật | ✅ Đúng | ❌ Sai |
|---|---|---|---|
| 1 | **Graphic không che dẫn chứng** (Q9) | Quay màn hình: `"side": "left"` + chữ chốt cột phải `{"x": 81, "w": 32, "pos": 34}`; trên bằng chứng chỉ `rings` / `freeze` | Chữ to đè lên cửa sổ, thẻ ảnh, khung video |
| 2 | **Quay màn hình không bao giờ làm nền mờ** | Muốn cho xem tool làm gì → `module: "screen"` hiện rõ | `bg_video: "assets/rec/…"` + `bg_blur` rồi phủ graphic lên |
| 3 | Nền mờ (`bg_video` + `bg_blur`) chỉ cho **cảnh trang trí** | Cảnh AI không mang thông tin (thành phố, bàn phím…) | Dẫn chứng thật làm nền |
| 4 | **Tiêu đề lớn đập ~1.2s rồi đi** (R5) | `title` + `p.then: [{module…}]` | Tiêu đề đứng 3–5s |
| 5 | **Gọi tên là có logo/ảnh** (Q2, 4b) | `callouts` logo app / ảnh thật bật đúng `cue` | Đọc "ElevenLabs" mà không có logo |
| 6 | **Không bịa** (Q1, C1) | Số có nguồn (`facts.json`), chữ chốt = ý đang đọc | Chữ chốt nói điều lời kể không nói, số không nguồn |
| 7 | Sub mặc định **`story_pop`**, từ đang đọc **vàng `#FACC15`** | `"subtitle": "story_pop"`, `palette[2]` vàng | Đổi màu/kiểu khi anh chưa yêu cầu |
| 8 | **Móc mới mỗi 5–8s**, không đoạn "câm hình" > 3s | Từ khoá / ring / callout / chuyển cảnh mới | Đoạn lặng 8s chỉ có 1 hình đứng |
| 9 | Không nền đen trơn > 2 cảnh liền (Q8) | Graphic đặt trên `bg_video` AI / ảnh thật | 3D trên nền đen suốt |
| 10 | **Luôn hậu kỳ CapCut**, SFX đúng giây; **không tự tắt CapCut** (hỏi anh) | `pipeline.py … capcut` khi CapCut tắt | Gửi thẳng bản FFmpeg; tự đóng CapCut |
| 11 | **Kiểm cuối bằng agent MỚI**, chỉ gửi khi `KẾT LUẬN: ĐẠT` | `pipeline.py … review` → Agent | Tự xem rồi gửi luôn |

Luật đầy đủ có mã số: [references/luat-dung.md](references/luat-dung.md). Tư duy dựng: [references/cong-thuc-edit.md](references/cong-thuc-edit.md). Tham số từng module: [references/modules.md](references/modules.md).

## 9 bước

### 1. Chẩn đoán → `edit_profile`
Đọc [../ai-semantic-video-editor/references/bo-nao-dao-dien.md](../ai-semantic-video-editor/references/bo-nao-dao-dien.md). Trả lời: thể loại, mục tiêu, khán giả, nền tảng (TikTok ≤90s → 9:16; YouTube → 16:9), cảm xúc, đường cảm xúc, độ nhạy cảm, cao trào ở đâu. Không hỏi anh trừ khi mơ hồ thật.

Ghi ra `edit_profile` đúng khung này (giá trị tiếng Việt không dấu, chọn 1):
```json
"edit_profile": {"genre": "giai_thich", "goal": "người xem biết …", "audience": "…", "platform": "tiktok_9x16_60s",
  "mood_key": "positive", "arc": ["tò mò", "bất ngờ", "tin tưởng"], "pacing": "vua", "emphasis": "stamp_slam",
  "subtitle": "story_pop", "sfx_style": "real_light", "climax_at": 0.8, "ending": "cta", "music_start": 0}
```
Script chỉ đọc 5 khoá: `mood_key` (`neutral|positive|fun|calm|tense|dark|shock|sad`), `emphasis`, `subtitle` (luôn `story_pop`), `sfx_style` (`cartoon|real_heavy|real_light|ui|minimal`), `music_start`. Các khoá còn lại để em tự định hướng kịch bản.

### 2. Dữ liệu thật → `facts.json`
`[{"fact": "...", "value": 176, "unit": "video", "source": "...", "url": "...", "date": "2026-11"}]`. Số không có nguồn → không đưa vào. Review phần mềm: nguồn = quay màn hình / đếm trong app, ghi ngày.
**Nguồn lệch nhau** (vd số đảo 1.600 / 1.969 / ~2.000): chọn nguồn gốc uy tín nhất, ghi ĐÚNG nguồn đó trên màn hình (`source`), lời kể dùng "khoảng / gần" nếu các nguồn chênh nhau. Chỉ ghi nguồn em đã mở đọc được; trang chặn (403) thì ghi nguồn trung gian em đã đọc (vd Wikipedia).

### 3. Kịch bản + storyboard
Mẫu: [templates/storyboard.example.json](templates/storyboard.example.json). Bắt buộc ở gốc: `"design": "v2"`, `"brand_tag"`, `"title"`, `"edit_profile"` (bước 1), và **khung hình**: `"canvas": [1080, 1920]` cho 9:16 (TikTok/Reels/Shorts, cũng là mặc định khi thiếu) hoặc `"canvas": [1920, 1080]` cho 16:9 (YouTube). Mẫu là 16:9 — làm dọc thì đổi `canvas`.
- Viết lời kể theo [../ai-semantic-video-editor/references/giong-ke-hay.md](../ai-semantic-video-editor/references/giong-ke-hay.md) (thú vị, có chất hài vừa đủ, hợp `edit_profile`). Mỗi scene 1 ý, 6–12s lời (`narration`). Mốc thời gian luôn ghi bằng `cue` (cụm từ có thật trong narration), không ghi giây.
- Hook đúng thể loại ([references/hook-thumbnail.md](references/hook-thumbnail.md)), cao trào 70–85% (`"climax": true`), kết = CTA đúng mục tiêu.
- Chọn module theo **loại thông tin**:

| Lời kể nói về… | Module |
|---|---|
| thao tác trên app / web (dẫn chứng) | `screen` (+ `side`, `rings`, `freeze`) |
| địa điểm | `map` (vệ tinh bay từ vũ trụ) |
| con số | `number`, `stats`, `dot_number`, `race`, `line_chart`, `waffle` |
| người / tổ chức | `dossier`, `people` + `callouts` ảnh thật |
| ảnh / sự kiện dẫn chứng | `photo`, `evidence`, `news` |
| trước → sau / so sánh | `compare`, `slider`, `duo`, `area_compare` |
| liệt kê / quy trình | `list`, `steps`, `icons`, `exploded3d`, `timeline`, `converge` |
| prompt → kết quả AI | `prompt_video` |
| câu mở chương | `title` + `p.then` |
| kêu gọi cuối video | `cta` |

Mỗi module "đinh" (3D, slider, timeline…) chỉ làm vai chính 1 lần/video (Q6). **Không để 2 cảnh liền nhau cùng module**: 2–4 số liệu cạnh nhau → gộp 1 cảnh `stats`; 1 số lớn → `number`/`dot_number`; số so quy mô → `area_compare`/`waffle`. **Năm** (2018, 1994) trong `number`/`stats` → thêm `"format": "year"` (không thì hiện "2.018"). "Hơn 1.400 m" → `"prefix": ">"` hoặc ghi "hơn" ở `label`, đừng nhét vào `unit`.
- Module `photo`: nguồn ảnh tự in từ credits — không đặt thêm `source`; `caption` ≤ 6 từ hoặc bỏ.
- **Ảnh thật**: KHÔNG đoán tên file. Tìm: `python $V/find_photo.py "Ha Long Bay" --out projects/<slug>/render/_find.jpg` → Read ảnh xem trước → ghi `"File:<tên đúng>"` vào `photo`/`bg_photo`. Mỗi cảnh một ảnh khác nhau. Logo tổ chức/app chưa có trong `brand/logos/`: `python $V/find_photo.py "UNESCO logo" --pick 1 --save .claude/skills/video-tai-lieu/brand/logos/unesco.png` rồi `callouts` dùng `"logo": "unesco"`.
- **Ảnh/video nền** (`bg_photo`/`bg_video`): ảnh là dẫn chứng (phong cảnh, công trình) → `"bg_dim": 0.15, "bg_blur": 0` để còn nhận ra (engine đã phủ thêm lớp tối của bộ khung); chỉ trang trí → `bg_dim` 0.35–0.45, `bg_blur` 4–8.
- **Cảnh `title`** luôn kèm `"title_hold": 1.2` và `p.then` — ví dụ:
```json
{"module": "title", "narration": "Năm 1994, UNESCO công nhận vịnh là di sản thế giới.",
 "p": {"title": "DI SẢN _THẾ GIỚI_", "title_hold": 1.2, "bg_photo": "File:…",
       "then": [{"module": "list", "cue": "công nhận", "p": {"items": [{"icon": "landmark", "text": "UNESCO · 1994", "cue": "UNESCO"}]}}]}}
```
- Cảnh `screen` có chữ chốt — mẫu chuẩn:
```json
{"id": "6", "module": "screen", "narration": "…dán cả danh sách prompt…",
 "p": {"video": "assets/rec/anh_ai.mp4", "src": [3440, 1392], "crop": [900, 60, 1700, 1250], "clip_start": 7.4, "rate": 0.5,
       "title": "Studio Ảnh AI · quay màn hình thật", "side": "left",
       "rings": [{"x": 1200, "y": 300, "w": 400, "h": 80, "label": "Nạp danh sách", "cue": "dán cả"}]},
 "keywords": [{"text": "DÁN CẢ DANH SÁCH", "cue": "dán cả danh sách", "effect": "zoom_big", "x": 81, "w": 32, "pos": 34, "size": 4.6}],
 "callouts": [{"logo": "elevenlabs", "name": "ElevenLabs", "cue": "ElevenLabs", "pos": "tr"}]}
```
`crop`, `rings` tính theo **toạ độ ảnh gốc** của bản quay (xem khung bằng `ffmpeg -ss <giây> -i rec.mp4 -frames:v 1 x.jpg` rồi Read). `clip_start` + `rate` chọn sao cho đúng lúc đọc `cue` thì màn hình đang hiện đúng thứ đó.
- Ảnh/thẻ minh hoạ cạnh bản quay → `callouts` với `"pos": {"x": 81, "y": 12}` (cột phải), `"size": 17`, `"ratio": 0.5625`, `"hold": 30`.
Nhịp `then` không lặp lại chữ của tiêu đề (tiêu đề "DI SẢN THẾ GIỚI" thì nhịp sau không đặt `title` "Di sản thế giới" nữa).
- Anh chưa nói "làm luôn" → gửi bảng duyệt: hồ sơ edit · logline · bảng `# | lời kể | dựng gì | chữ chốt | nguồn`.

### 4. Giọng kể
`python $A/tts_macro.py projects/<slug>/storyboard.json --auto` → `narration/voice.mp3`, `words.json`, `sync.json`. Mỗi lượt ≤1000 ký tự. Trước khi bấm tạo phải thấy đúng tên giọng trong panel. Chưa có tool: `python $A/story_voice.py … --provisional` để dựng thử.

### 5. Tư liệu
`python $V/fetch_assets.py projects/<slug>/storyboard.json` (bản đồ, ảnh Wikimedia, icon, cờ, viền quốc gia). Quay màn hình app: ffmpeg gdigrab. Cảnh AI / ảnh AI: dùng macro trong CLAUDE.md (`auto_tool.py`, `image_macro.py`). **Read từng ảnh tải về**: đúng người/nơi, không watermark, không phản cảm.

### 6. Kiểm bố cục + luật — chạy sau MỖI lần sửa storyboard
```
python $V/pipeline.py projects/<slug> check
python $V/pipeline.py projects/<slug> stills 12.5 40 88      ← mỗi cảnh 1 mốc: giữa cảnh (start + 60% thời lượng, xem bảng giây trong output `check`), rồi Read từng ảnh
```
Cổng qua: `OK: check xong`. Xem ảnh stills: chữ đủ dấu, không che bằng chứng, bản quay hiện đúng thao tác lúc đọc.

### 7. Render (lâu — chạy nền `run_in_background`)
`python $V/pipeline.py projects/<slug> render` → `render/video.mp4` + bản FFmpeg trong `2-xuat/`. ~4–5 giây máy cho 1 giây video (5 phút video ≈ 20 phút). Không tốn hạn mức AI. Trong lúc chờ: làm thumbnail (`python $V/thumbnail.py projects/<slug>/storyboard.json`, 2–3 phương án, xem `render/_thumbs_check.jpg`).

### 8. Hậu kỳ CapCut + kiểm cuối
1. CapCut đang mở → **hỏi anh tắt**. Rồi: `python $V/pipeline.py projects/<slug> capcut` → cổng `OK: draft … sẵn sàng`.
2. `python $V/pipeline.py projects/<slug> review` → làm đúng lời nhắn nó in ra: giao **một agent MỚI** (chạy nền) soát. Báo cáo `CẦN SỬA` → sửa storyboard → `check` → `render` → `capcut` → `review` (agent mới khác).
3. Khi `KẾT LUẬN: ĐẠT`: mở CapCut (computer use) → mở project `<title> (hau ky)` → **Xuất** (góc trên phải) → **Xuất** trong hộp thoại (1080p) → chờ file trong Downloads.

### 9. Hoàn tất
`python $V/pipeline.py projects/<slug> finish` → chặn đỉnh âm, ghi `2-xuat/<title> (hau ky).mp4`. Gửi anh (SendUserFile) video + `thumbnail_*.jpg` + 3 dòng: hồ sơ edit, nguồn chính, điểm nhấn. Không tắt CapCut. Chỉ dọn file tạm khi anh OK.

## Gặp lỗi thì làm gì

| Dòng báo | Cách sửa |
|---|---|
| `chữ chốt che bằng chứng` | Cảnh `screen`: thêm `"side": "left"` + chữ chốt `x: 81, w: 32`; cảnh thẻ/ảnh: dời `pos` lên dải trống |
| `quay màn hình … bị làm NỀN mờ` | Đổi cảnh đó sang `module: "screen"`, hoặc thay `bg_video` bằng cảnh AI trang trí |
| `tiêu đề lớn treo` | Thêm `p.then` (xem modules.md mục *title*) |
| `gọi tên 'X' nhưng chưa có logo` | Thêm `callouts` logo (thư mục `brand/logos/`) đúng `cue` |
| `có thứ bật lên … chỉ 0.xs trước khi cắt` | Đổi `cue` sớm hơn hoặc bỏ phần tử đó |
| `chữ đè nhau / tràn / nhỏ` | Sửa `pos`, `size`, `x/w`; xem `render/qa_*.jpg` |
| `Cần xem lại cue` (plan_timeline) | `cue` không khớp lời đọc → chép đúng cụm từ trong narration |
| `CapCut đang mở` | Hỏi anh tắt; không tự tắt |
| `thiếu mẫu tiếng` | Báo anh tải mẫu SFX đó trong CapCut |
| Video trong `screen` trống đen | Hai cảnh dùng chung 1 file video → copy file ra tên khác cho cảnh thứ hai |

## Ranh giới
Không bịa số, trích dẫn, ảnh. Không ảnh máu me thật. Ảnh người thật chỉ từ nguồn công bố, có ghi nguồn. Không chép nhận diện kênh khác (dùng `brand/brand.json`). An toàn tool AI VIDEO LIBRARY: theo CLAUDE.md (chỉ click / Ctrl+A / Ctrl+V / Esc; không đăng nhập, mua gói thay anh).
