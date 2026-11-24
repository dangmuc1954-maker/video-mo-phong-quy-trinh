# Danh mục dựng: module · bộ khung · tông · hiệu ứng từ khoá · chuyển cảnh

Chữ trong mọi trường text: `*từ*` = màu nhấn 1 (cam), `_từ_` = màu nhấn 2 (vàng), `\n` = xuống dòng.
Thời điểm: mọi object có `"cue": "cụm từ trong lời kể"` → engine dùng giây cụm đó được đọc (`plan_timeline.py` đổi thành `at`). Trường kiểu `tag_cue`, `photo_cue` → `tag_at`, `photo_at`.

## Module (lớp 2 — loại thông tin)

| module | Dùng khi lời chạm tới | `p` chính |
|---|---|---|
| `map` | địa danh, vị trí, đường đi, khoảng cách | `places:[{name|lat,lon, zoom:12, label, cue, move:1.8, arc:1}]` (điểm đầu = mở cảnh; điểm sau bay tới khi đọc `cue`), `from_space:true` (lần đầu nhắc địa danh trong video), `space_dur:2.8`, `routes:[{points:[[lat,lon],…], color, dash, value, unit, label, cue, dur}]`, `kicker`, `title`, `drift` |
| `title` | mở chương, tuyên bố, tiêu đề lớn | `pill` (dòng nhỏ • •), `kicker`, `title`, `subtitle`, `size`, `tag` (nhãn vàng), `tag_cue` |
| `number` | một con số quan trọng | `value`, `format: "year"` (năm, không dấu chấm), `sep`, `prefix`, `unit`, `decimals`, `label`, `note`, `source`, `cue` (lúc số bắt đầu chạy), `count` (giây chạy), `kicker`, `title` |
| `stats` | 2–4 con số cùng nhóm (quy mô) | `items:[{icon, value, unit, label, cue}]`, `kicker`, `title`, `source`, `bottom` |
| `list` | liệt kê A, B, C / quy trình | `items:[{text, icon, check, cue}]`, `flow:true` (ô → mũi tên → ô), `kicker`, `title`, `top` |
| `steps` | bài học / lưu ý đánh số | `total`, `active`, `title`, `points:[{text, cue}]` |
| `compare` | A vs B, trước / sau | `left/right:{kicker, title, value, unit, lines, photo|photo_query, cue}`, `vs`, `source` |
| `icons` | tiện ích, đặc điểm | `items:[{icon, label, cue}]`, `cols`, `photo|photo_query`, `photo_caption`, `photo_cue`, `source` |
| `photo` | ảnh thật / bằng chứng / địa điểm | `photo|photo_query`, `caption`, `source`, `bw`, `rot`, `kicker`, `title` |
| `dossier` | nhân vật lần đầu được nhắc | `photo|photo_query` (không có → bóng đen "?"), `name`, `alias`, `role`, `facts:[...]`, `file_label`, `source` |
| `news` | biến cố, sự kiện báo đưa | `masthead`, `date`, `headline`, `body`, `photo`, `labels:[{text, small, style:red|black|yellow, cue, x, y, size, rot}]` |
| `question` | câu hỏi mở, twist, trích lời | `text`, `quote:true`, `by`, `size`, `tag`, `tag_cue` |
| `evidence` | đông / vượt kế hoạch / trước–sau có ảnh thật | `before:{photo, label:"DỰ KIẾN", caption}`, `after:{photo, source, label:"THỰC TẾ", caption, stat:{value,prefix,unit}, stat_cue, stamp:{text, cue, color}}`, `cue` (lúc mũi tên quét sang ảnh thực tế), `kicker`, `title`, `source` |
| `cta` | kêu gọi comment | `title`, `text`, `keyword` |
| **`race`** (v2) | so 2–4 giá trị cùng đơn vị: ai giàu/nhanh/đông hơn | `items:[{label, flag:"sg", value, prefix, unit, decimals, color, cue}]`, `max`, `badge:{text, cue}`, `dur`, `kicker`, `title`, `source` |
| **`line_chart`** (v2) | tăng trưởng theo năm (số liệu thật) | `series:{"1965":517,…}`, `prefix`, `unit`, `decimals`, `y_max`, `ticks`, `cue` (lúc bắt đầu vẽ), `dur`, `badge:{text:"×183", cue}`, `color`. Nhãn đầu bút CHỈ hiện mốc có trong `series` (không bịa số nội suy) |
| **`area_compare`** (v2) | "nhỏ bằng 1/5 Hà Nội", quy mô | `small:{kicker, label, value, unit, decimals, note, color, cue}`, `big:{label, value, unit}`, `parts`, `frac`, `cue` (lúc tô phần nhỏ), `source` |
| **`strike_cards`** (v2) | "không có A, không có B…" | `items:[{text, icon, color, cue, strike_cue, stamp, note}]`, `stamp:"KHÔNG CÓ"`, `kicker`, `title`, `source` |
| **`quote`** (v2) | trích lời nhân vật trên nền ảnh/tranh | `text` (`
`, `_vàng_`), `by`, `caption` ("Tranh minh hoạ" khi nền là ảnh AI), `size`, + `bg_photo` |
| **`open_loop`** (v2) | câu hỏi treo giữ người xem | `title`, `cards:["BÍ QUYẾT #1",…]` hoặc `n` + `card_label`, `cue` (lúc thẻ bật) |

**Bản đồ v2 — lớp phủ lên ảnh vệ tinh (module `map`):** `borders:[{iso:"MYS", color:"#6EA8FF", fill:.16, width:.35, cue}]` (viền quốc gia phát sáng + tô nhẹ, dữ liệu geoBoundaries tự tải), `split:{iso:"SGP", cue, dx:3, dy:5, line:[[lat,lon],[lat,lon]]}` (mảng ảnh vệ tinh của nước đó tách rời theo đường cắt vàng), `marks:[{label, lat, lon, color, cue, dx, dy, hold, iso}]` (nhãn tròn: sông, quận, nước; `dx/dy` theo đơn vị U để né nhãn khác; `iso` = đi theo mảng đất tách), `header_cue` (lúc hiện tiêu đề), place `"pin": false` (ẩn ghim). Đường tuyến v2: vàng phát sáng, đầu tàu chạy, ô số km (`chip_at` 0–1 = vị trí dọc tuyến). Mép các mức zoom tự mờ dần (không lộ khung).

**Ảnh / video thật cho MỌI module:** `p.bg_photo` (nền, tự zoom chậm, tối đi theo `bg_dim` 0.3–0.5, `bg_source` ghi nguồn góc trên) hoặc `p.bg_video` (`bg_start`, `bg_rate`). Giá trị ảnh: `"File:<tên file Wikimedia>"` (đã chọn bằng mắt), URL ảnh báo/trang chính thức (kèm `source`), hoặc link bài mạng xã hội / YouTube / TikTok cho `bg_video` (yt-dlp tải, kèm `bg_source`). `photo_query` = để script tự tìm trên Commons (phải xem lại ảnh).

Icon: tên Lucide (lucide.dev/icons), ví dụ `map-pin`, `ruler`, `users`, `building-2`, `train-front`, `car`, `clock`, `trees`, `waves`, `ship`, `landmark`, `scale`, `banknote`, `flask-conical`, `atom`, `shield-alert`, `newspaper`, `gavel`.

## Bộ khung (lớp 1 — `theme` của scene, theo chủ đề / chương)
`dark_glow` (giải thích, công nghệ, tổng quát) · `map` (tự dùng cho module map) · `news` (tin tức, sự kiện) · `dossier` (vụ án, bí ẩn, lịch sử nhân vật) · `lab` (hoá học, khoa học, y học) · `finance` (tài chính, giá cả) · `plain`.
Chưa có bộ khung cho chủ đề cần dùng (bếp, thể thao, toà án…) → thêm class `.th-<tên>` vào `templates/engine.html` theo bảng lớp 1 trong cong-thuc-edit.md, giữ màu nhấn và font của brand.

## Tông (lớp 3 — `mood` của scene)
`neutral` · `positive` (sáng ấm) · `fun` (tươi, cho hoạt hình / vui) · `calm` (chữa lành) · `tense` (căng thẳng: tối, rung nhẹ, hạt) · `dark` (đẫm máu / rùng rợn: giảm màu, rung, hạt, viền đỏ thẫm — KHÔNG ảnh phản cảm) · `shock` (rung mạnh) · `sad` (lạnh, nhạt).

## Hiệu ứng từ khoá (`keywords[].effect` — theo NGHĨA của từ)
| effect | Nghĩa | Ghi chú |
|---|---|---|
| `stamp_slam` | chấn động, nghiêm trọng, bê bối, kết luận mạnh | mảnh giấy đỏ xé đập xuống + rung; `color` đổi màu giấy |
| `giftbox` | rẻ, ưu đãi, quà, khuyến mãi | rung → hộp quà → giá bay ra + confetti |
| `count` | đắt, số tiền lớn, số liệu nói nhanh | `value`, `prefix`, `unit`, `decimals` |
| `rise` | tăng, tăng trưởng, vươn lên | màu xanh mặc định |
| `crack` | giảm, sụp đổ, thất bại, phá sản | đỏ, nứt rơi |
| `warning` | nguy hiểm, độc hại, cấm, cảnh báo | sọc vàng đen nhấp nháy |
| `redact` | bí mật, che giấu, sự thật | thanh đen trượt mở |
| `speed` | nhanh, tốc độ, chỉ X phút | lao vào có vệt mờ |
| `typewriter` | căng thẳng, chậm, hồ sơ, mốc thời gian | gõ từng ký tự |
| `zoom_big` | khổng lồ, quy mô | phóng từ nhỏ |
| `bounce` | vui, hài, dễ thương (hoạt hình) | chữ viền đen nảy lắc |
| `fade` | ấm áp, suy ngẫm, chữa lành | hiện mờ dần |
| `year_roll` (v2) | "17 năm chờ đợi", mốc thời gian dài | `from`, `to`, `roll` (giây chạy) → "2007 → 2024" năm chạy lên |
Chung: `text` (chữ chính), `sub` (chữ phụ nhỏ phía trên, viết nghiêng), `cue`, `hold` (giây, mặc định 1.9), `pos` (`upper`/`center`/`lower`), `size`, `color`.

## Chuyển cảnh (`transition_in`)
`cut` · `fade` (êm) · `whip` (lia nhanh, mặc định giữa ý) · `zoom` (đi sâu vào) · `flash` (lóe trắng, phát hiện) · `flash_red` (sốc, bạo lực) · `slam` (đập vào, kết luận) · `pop` (vui) · `black` (chương nặng nề).
`capcut_transition`: tên chuyển cảnh CapCut muốn thêm khi hậu kỳ (vd "Phóng to rồi mờ dần") — chỉ khi hợp tông.

## Camera (`camera`)
`push` (mặc định, đẩy chậm) · `push_fast` · `static`. Tông `tense/dark/shock` tự thêm rung.

## SFX (`sfx`)
`[{"cue": "...", "sound": "mô tả", "search": "từ khoá EN", "volume": 0.4, "why": "..."}]` — chỉ cho hành động/âm thanh có thật trong câu. SFX theo hiệu ứng từ khoá và chuyển cảnh được thêm tự động theo `edit_profile.sfx_style`.

## callouts — logo / ảnh thật bật đúng lúc đọc tên (quy tắc 4b, BẮT BUỘC)
Mỗi cảnh có thể khai `"callouts"` (ngoài `p`). Gọi tên phần mềm/app → **logo chính thức**; tổ chức/sự vật cụ thể → **ảnh thật có nguồn**.
```json
"callouts": [
  {"logo": "claude", "name": "Claude", "cue": "Claude", "pos": "top", "hold": 3},
  {"items": [{"logo": "veo", "name": "Veo 3", "cue": "Veo 3"}, {"logo": "google", "name": "Google", "cue": "của Google"}], "pos": {"x": 50, "y": 13}},
  {"photo": "assets/img/collins.jpg", "name": "Từ điển Collins", "source": "Collins Reference / CC BY-SA 4.0", "cue": "từ điển Collins", "pos": {"x": 14, "y": 14}, "size": 23, "ratio": 1.36}
]
```
- `logo`: khoá trong `brand/logos/<khoá>.png` (thư viện dùng chung: openai, chatgpt, claude, google, veo, grok, elevenlabs, capcut, mckinsey, ai-video-library…) hoặc đường dẫn trong dự án. Thiếu logo → tải bản chính thức (Wikimedia Commons / trang hãng) bỏ vào `brand/logos/`.
- `photo`: đường dẫn hoặc khoá ảnh trong assets.json; luôn kèm `source`. Liệt kê sự vật (bò, ngựa…) → mỗi thứ một item, `cue` đúng chữ.
- Không có logo chính thức → chỉ `name` (hiện thẻ chữ).
- `pos`: tl | tr | top | center | bl | br | {x,y} (%, x là tâm thẻ). `size` (U), `name_size`, `hold`, `until`.
- plan_timeline cảnh báo `! … gọi tên 'x' mà chưa có callout logo`; qa_layout kiểm cả khung thẻ (đè/tràn). SFX gợi ý "pop" tự thêm.

## title — tiêu đề lớn CHỈ ĐẬP ~1.2s rồi nhường chỗ cho nhịp graphic (BẮT BUỘC, anh yêu cầu 11/11/2026)
Không để tiêu đề lớn treo đơ nhiều giây. Cảnh `title` dài > 2.6s phải có `p.then` (plan_timeline in `!` nếu thiếu):
tiêu đề hiện `title_hold` (mặc định 1.2s, có thể `title_cue` để hiện đúng lúc đọc) → bay ra (phóng to + nhoè) → các nhịp graphic
diễn đúng câu đang đọc, mỗi nhịp có `cue` (nhịp đầu mặc định nối ngay sau tiêu đề).
```json
"p": {"title": "~45% code AI\n*có lỗ hổng*", "title_hold": 1.2, "then": [
  {"module": "waffle", "p": {"value": 45, "cue": "bốn mươi lăm", "caption": "code AI viết\n_có lỗ hổng_", "caption_cue": "lỗ hổng", "source": "…"}},
  {"module": "duo", "cue": "dùng cho việc riêng", "p": {"items": [{"icon": "user", "title": "Việc riêng", "verdict": "Tuyệt", "tone": "ok", "cue": "việc riêng"},
                                                              {"icon": "building-2", "title": "Việc lớn", "verdict": "Cần người kiểm", "tone": "warn", "cue": "việc lớn"}]}}]}
```
Nhịp nào cũng dùng được mọi module (list flow, stats, icons, compare, screen…) + 6 module nhịp mới:
| module | khi nào | tham số chính |
|---|---|---|
| `converge` | "hàng triệu người → một AI", "1 người làm việc của cả ê-kíp" | `center{icon,text,cue}`, `items[{icon,label,cue}]` (vai trò bay vào lõi lúc `merge_cue`), `particles` (hạt chảy vào lõi), `kicker` |
| `transform` | "không biết X → vẫn làm được Y", cũ → mới | `from{icon,text,strike_cue}` (bị gạch), `arrow_cue`, `to{icon,text,cue}` (sáng + ✓) |
| `waffle` | tỉ lệ % dễ hình dung (45/100) | `value`, `total`, `cue`, `color`, `caption`, `caption_cue`, `source` |
| `duo` | hai trường hợp / hai phán định | `items[{icon,title,verdict,tone:ok/warn/bad,cue}]` |
| `prompt_video` | "chỉ một dòng mô tả → video" | `prompt{text,cue,speed}` (ĐÚNG câu lệnh đã tạo clip), `video` + `video_cue`, `chips[{icon,text,cue}]`, `ring_cue`, `caption` (ghi rõ nguồn clip) |
| `people` | "ai cũng làm được…" | `n`, `badge_cue`, `badge_icon`, `caption{text,cue}`, `strike{text,cue,strike_cue}` (điều kiện cũ bị gạch) |
Chọn nhịp theo NGHĨA câu thoại (không lấy cho có): số % → waffle; đối lập cũ/mới → transform; hội tụ/quy mô → converge; liệt kê vai trò/bước → list flow.

## Chuyển động mới (11/11/2026, học từ video-shotcraft — Apache-2.0, viết lại cho engine HTML, không chép mã)
Dùng như module thường hoặc làm nhịp trong `p.then` của title. Mọi mốc ghi bằng `cue`. Mỗi kiểu "đinh" chỉ 1 lần / video (luật Q6).
| module | khi nào | tham số chính |
|---|---|---|
| `breakout` | "tăng vượt mọi kỷ lục": đường số liệu leo, điểm cuối VỌT qua trần cũ, khựng rồi trục y đổi thang | `points[{x,v}]`, `ceiling`, `cue` (lúc vọt), `unit/prefix/decimals`, `ceiling_label`, `kicker/title`, `source` |
| `dot_number` | "900 triệu người": hàng trăm chấm (mỗi chấm một người) bay lượn rồi gom thành con số | `text`, `cue`, `color`, `caption{text,cue}`, `kicker` |
| `timeline` | lịch sử / tiểu sử / các bước: máy quay lướt ngang, mỗi mốc bật thẻ đúng lúc đọc | `events[{label,text,icon/photo,cue}]`, `kicker` |
| `slider` | trước / sau (quy hoạch, công trình, trước–sau AI) | `before{photo,label}`, `after{photo,label}`, `cue`, `rest` (vị trí dừng %, mặc định 50), `source` |
| `orbit3d` | 3D băng chuyền thẻ: nhiều tính năng / thành phần, vòng xoay dừng đúng thẻ đang đọc | `items[{icon/photo,label,cue}]`, `step` (độ giữa 2 thẻ), `tilt`, `kicker` |
| `exploded3d` | 3D tách lớp: cấu tạo nhiều tầng (bộ skill, kiến trúc, quy trình), tách theo chiều sâu, nhãn từng lớp đúng lúc đọc | `layers[{label,icon,color,cue}]` (dưới→trên), `explode_cue`, `merge_cue`, `kicker` |
| `flying_words` | liệt kê nhiều khái niệm trừu tượng: từ khoá bay từ xa qua sát ống kính | `words[]`, `speed`, `kicker` |

**Thêm vào module có sẵn (không đổi cách cũ):**
- `title`: `"title_exit": "label"` → tiêu đề co 0.3x bay về góc trái trên và Ở LẠI làm nhãn mục của đoạn (mặc định vẫn là bay ra). `label_scale` chỉnh cỡ nhãn. Tiêu đề thu nhãn nên ≤ 3–4 từ.
- `screen`: `"freeze": [{cue, dur, label, x, y, w, h}]` → video DỪNG HÌNH đúng lúc đọc, chớp sáng, khoanh vàng + nhãn (toạ độ ảnh nguồn như `rings`), rồi chạy tiếp từ đúng chỗ dừng.
- cảnh bất kỳ `"climax": true` → plan_timeline tự thêm câu âm thanh riser → impact → sparkle (luật S5).
- storyboard `"sub_size"` (đơn vị U) ghi đè cỡ sub; v2 khổ ngang mặc định 4.4.

## Bố cục cảnh có bằng chứng (luật Q9 — graphic không che dẫn chứng)
- `screen`: `"side": "left" | "right"` → cửa sổ quay màn hình rộng ~60%, dồn một bên, chừa cột cho chữ chốt. Không ghi `side` = căn giữa như cũ.
- Từ khoá (`keywords`) đặt theo cột: `"x"` (tâm, % ngang) + `"w"` (rộng, %), `"pos"` (% dọc). Ví dụ cột phải: `{"text": "CHẠY NGẦM", "cue": "chạy ngầm", "x": 82, "w": 30, "pos": 38}`.
- Vùng bằng chứng được engine đánh dấu `.qa-ev`: cửa sổ `screen`, khung video `prompt_video`, thẻ `timeline`, khung `slider`. `qa_layout` báo lỗi khi chữ chốt đè lên.
- Muốn chỉ vào chi tiết trên bằng chứng → dùng `rings` / `freeze` (viền), không dùng chữ to đè lên.
