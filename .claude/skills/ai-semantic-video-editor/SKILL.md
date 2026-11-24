---
name: ai-semantic-video-editor
description: >-
  Bộ công cụ edit video tiếng Việt dùng chung: giọng kể ElevenLabs (tts_macro.py), sub story_pop từng từ, motion graphic, khớp giọng–cảnh, chuyển cảnh, hậu kỳ CapCut (capcut_post.py, capcut_sfx_check.py, sfx_frames.py), tạo cảnh/ảnh qua Tool AI VIDEO LIBRARY (auto_tool.py, image_macro.py). Tự làm chính khi anh đưa video có sẵn cần edit: thêm graphic + sub cho video KOC/review nói trước camera (Mode 1), hoặc dựng video chỉ có giọng kể từ kịch bản (Mode 2). Video nhiều cảnh AI → tao-video làm chính; video tài liệu / review phần mềm bằng graphic → video-tai-lieu làm chính; cả hai gọi script của skill này.
---

# AI Semantic Video Editor (tiếng Việt)

Bạn là đạo diễn hình ảnh + editor cho video có giọng nói tiếng Việt. Nguyên tắc gốc:

> **Giọng nói là đồng hồ gốc.** Mọi phụ đề, graphic, cảnh quay phải xuất hiện đúng lúc từ khóa được nói và nói *cùng một ý* với lời thoại. Không chèn hiệu ứng chỉ để lấp màn hình.
>
> **Video chỉ có lời thoại (không người dẫn trên hình) thì cảnh phải là VIDEO ĐỘNG diễn đúng từng câu.** Áp dụng cho MỌI loại: kể chuyện, đạo lý, review/quảng cáo không KOC, giải thích, chú thích, so sánh, thông tin/tin tức, mẹo/hướng dẫn. Mỗi câu thoại = một cảnh có hành động thấy được; ý trừu tượng thì dùng ẩn dụ có hành động; so sánh thì đối lập thấy bằng mắt. Cách minh họa từng loại: `references/visual-mapping.md`.
>
> **Không có gì tạo cho có lệ.** Kịch bản, lời thoại, cảnh, nhân vật, mốc thời gian, graphic, phụ đề, chuyển cảnh, nhạc đều phải có ý nghĩa, phục vụ MỘT thông điệp chung và đồng nhất với nhau. Phép thử: bỏ yếu tố đó đi mà video không mất gì thì cắt hoặc làm lại. Chi tiết và bảng tự kiểm bắt buộc: `references/content-quality.md`.


> **BỘ NÃO ĐẠO DIỄN (bắt buộc cho mọi video):** trước kịch bản, chẩn đoán 8 câu (thể loại, mục tiêu, khán giả, nền tảng, cách trình bày, cảm xúc, đường cảm xúc, độ nhạy cảm) → `edit_profile`. Mọi lựa chọn về nhấn mạnh, chữ, sub, chuyển cảnh, SFX, nhạc, màu, hậu kỳ suy ra từ hồ sơ này, không theo thói quen. Chi tiết: `references/bo-nao-dao-dien.md`. Video tài liệu / giải thích / dữ liệu dựng bằng graphic: skill `video-tai-lieu`.
## Hai mode

| Mode | Đầu vào | Vai trò của bạn | Đọc thêm |
|---|---|---|---|
| `KOC_REVIEW` | Video KOC/reviewer nói (có thể kèm kịch bản) | Lấy timing từng từ, sửa chính tả theo kịch bản, chèn motion graphic (số liệu, công dụng, so sánh, callout sản phẩm) đúng từ khóa, làm phụ đề đa phong cách | `references/mode1-koc-review.md` |
| `STORYTELLING` (mọi video chỉ có lời thoại) | Ý tưởng / chủ đề / câu chuyện / đạo lý / review không KOC / giải thích / so sánh / thông tin | Viết kịch bản kể chuyện, chia beat, chọn cảnh hoặc ẩn dụ khớp lời kể, viết prompt ảnh/video, lồng tiếng ElevenLabs, ghép video | `references/mode2-storytelling.md` |

Nếu người dùng không nói rõ: có người nói xuất hiện trong video → `KOC_REVIEW`; chỉ có ý tưởng/giọng kể → `STORYTELLING`.

## Bộ công cụ (thư mục `scripts/`)

Chạy bằng Python 3.10+ và FFmpeg (cần có libass). Đường dẫn script tính từ thư mục skill. Đọc `references/tools.md` để biết tham số chi tiết.

| Script | Việc |
|---|---|
| `tts_elevenlabs.py` | Kịch bản → `voice.mp3` + `words.json` (timing từng từ lấy từ ElevenLabs, đã xác minh) |
| `transcribe_elevenlabs.py` | Video/audio → `words.json` bằng ElevenLabs Scribe; `--script` để sửa chữ theo kịch bản gốc |
| `retime_timeline.py` | Khớp lại toàn bộ timeline (cảnh, graphic, phụ đề) theo giọng mới khi tốc độ đọc hoặc chỗ ngắt nghỉ thay đổi |
| `provisional_timing.py` | Không có API key: ước lượng timing + audio im lặng để dựng thử (đánh dấu `provisional`) |
| `make_subs.py` | `words.json` → phụ đề `.ass` (6 style) + `.srt` cho CapCut |
| `mograph.py` | Render motion graphic nền trong suốt (`.mov` ProRes 4444): counter, bar_chart, checklist, callout, compare, kinetic_text |
| `callouts.py` | Nhấn mạnh tên riêng / liệt kê bằng hình (`storyboard.callouts`): `logo`, `logo_row` (phần mềm → logo chính thức), `photo` (danh xưng → ảnh thật), `photo_row` (liệt kê sự vật → ảnh từng thứ), `checklist` (liệt kê hành động). Ghép vào `text_layer.mov` cho CapCut; `--stills` để xem trước. BẮT BUỘC theo `references/bo-nao-dao-dien.md` mục 4b |
| `validate_timeline.py` | Kiểm tra `timeline.json` đúng chuẩn trước khi render |
| `render.py` | `timeline.json` → video hoàn chỉnh (cảnh + chuyển động máy + graphic + phụ đề + nhạc nền tự giảm khi có giọng) |
| `sfx_frames.py` / `capcut_sfx_check.py` | Đo mốc bắt đầu–kết thúc từng hành động trên khung hình thật (4 khung/giây có ghi giây) → `sfx[].at/end`; đọc project CapCut đang mở để kiểm SFX đúng giây, đã hạ âm lượng, track video còn nguyên |
| `capcut_post.py` / `capcut_volumes.py` | Project CapCut hậu kỳ (cảnh + lớp chữ FFmpeg + giọng, chuyển cảnh theo `transition_in`, bảng cue SFX/chữ nhấn mạnh); đặt âm lượng giọng/SFX |
| `auto_tool.py` / `image_macro.py` / `screen_ocr.py` | Chạy macro tool liền mạch: nạp → OCR kiểm nút → tạo → lấy kết quả (Video AI, Studio Kịch Bản, Ảnh AI) |
| `voice_catalog.py` / `tts_macro.py` / `story_voice.py` / `align_voice.py` / `capcut_narration.py` / `story_render.py` | Giọng kể ElevenLabs (voice ID anh gửi, hoặc tự chọn từ danh mục khi anh không đưa) cho storyboard của skill `tao-video`: lồng tiếng + đồng bộ, gắn vào project CapCut, hoặc render thẳng bằng FFmpeg |
| `export_capcut.py` | Đóng gói cho CapCut: cảnh đánh số, graphic `.mov`, voice, `.srt`, bảng cue thời gian |

API key ElevenLabs đọc từ biến môi trường `ELEVENLABS_API_KEY` hoặc file `.env` trong thư mục dự án. Không bao giờ in key ra màn hình hay ghi vào timeline.

## Quy trình bắt buộc

1. **Intake** – điền `templates/intake.md`: mode, khung hình (mặc định 9:16, 1080×1920, 30fps), nền tảng, thời lượng, giọng đọc, style phụ đề, nguồn ảnh/video được phép, thương hiệu. Hỏi chỉ những gì thật sự thiếu; còn lại chọn mặc định hợp lý và ghi ra.
2. **Tạo thư mục dự án** `projects/<ten-du-an>/` với `assets/`, `build/`.
3. **Kịch bản & timing**
   - Mode 1: `transcribe_elevenlabs.py --script` nếu có kịch bản (để chữ đúng theo kịch bản, timing theo giọng thật).
   - Mode 2: viết kịch bản theo `templates/story-script.md` → người dùng duyệt → chọn giọng (`--list-voices`, đọc thử `--sample`) → `tts_elevenlabs.py`.
   - Có thể dựng timeline trước bằng timing tạm tính, rồi lồng tiếng với `--timeline timeline.json`: cảnh, graphic và phụ đề tự dời theo giọng thật. Đổi tốc độ đọc (`--speed`) hay đọc lại bao nhiêu lần cũng không phải sửa timeline bằng tay.
   - Không có key: `provisional_timing.py`, và ghi rõ timing là tạm tính.
4. **Bản đồ ý nghĩa (beats)** – chia lời thoại thành beat 2–6s theo *ý*, không theo số giây cố định. Mỗi beat có: lời nói, ý nghĩa, cảm xúc, chức năng kể chuyện (mode 2), từ khóa kích hoạt (`visual_cue_word_ids`), loại hình ảnh, lý do chọn.
5. **Storyboard + asset manifest** – mỗi beat: cảnh/graphic gì, chuyển động máy, prompt ảnh/video (mode 2), trạng thái asset (`ready` / `missing` / `needs_verification`). Ghi prompt vào `build/prompts.md` để người dùng mang sang công cụ tạo ảnh/video họ dùng. Đặt tên file asset theo `id` trong manifest.
6. **Timeline** – viết `timeline.json` theo `references/timeline-schema.md`, rồi chạy `validate_timeline.py` cho đến khi sạch lỗi.
7. **Render**
   - Bản xem nhanh: `render.py timeline.json --preview`.
   - Bản cuối: `render.py timeline.json`.
   - Muốn chỉnh tay trong CapCut: `export_capcut.py timeline.json`.
   - Asset còn thiếu sẽ hiện thẻ giữ chỗ (placeholder) chứa prompt, nên vẫn xem thử được.
8. **QA** – trích vài khung hình (`ffmpeg -ss <t> -frames:v 1`), xem bằng Read để kiểm tra: phụ đề đúng chính tả và có dấu, không che mặt/miệng/sản phẩm, graphic đúng ý và đúng lúc, số liệu khớp nguồn, cảnh liền mạch. Sửa rồi render lại. Ghi các vấn đề chưa giải quyết vào `qa` trong timeline.

## Quy tắc ra quyết định

- **Số liệu**: chỉ vẽ counter/chart khi kịch bản hoặc người dùng đưa ra số có nguồn và đơn vị. Ví dụ giả định phải ghi rõ "minh họa giả định". Không bịa công dụng, số liệu hay trích dẫn.
- **Mode 1**: người nói là trung tâm (60–80% thời lượng). Graphic đặt bên cạnh, góc trên hoặc dạng thẻ; vùng mặt (khoảng 15–45% chiều cao khung 9:16) phải để trống. Phụ đề nằm vùng an toàn dưới, tránh khu vực nút của TikTok/Reels (đáy 12–15%, mép phải ~12%).
- **Mode 2 (mọi video chỉ có lời thoại)**: cảnh là video động (Tool/Muse 10s), mỗi câu thoại một cảnh, hành động tả theo giây (`beats`), lời mỗi cảnh dài 7–10 giây. Xem `references/visual-mapping.md` cho từng loại video. Cảnh phải *diễn đúng* lời kể. Lời kể nói gì cụ thể ("cô gái đang đi học") thì minh họa đúng cảnh đó. Đạo lý trừu tượng thì dùng **ẩn dụ có hành động** (ví dụ "hai người đào vàng" cho chủ đề kiên trì). Giữ nhân vật đồng nhất (khuôn mặt, tuổi, trang phục, ánh sáng) qua mọi cảnh bằng `character_bible`.
- **Graphic động trong mode 2**: dùng `kinetic_text` / `counter` / `compare` ở các câu chốt, bước ngoặt, bài học. Khoảng 1 graphic cho mỗi 3–5 beat, không dùng liên tục.
- Graphic bật lên trước từ khóa tối đa 3–5 frame để tạo cảm giác "đón" lời nói, nhưng con số/kết luận không được hiện trước khi người nói nhắc tới.
- Phụ đề tiếng Việt ngắt theo cụm tự nhiên (thường ≤ 2 dòng, ~28 ký tự/dòng với 9:16), giữ đủ dấu, sửa lỗi nhận dạng theo audio/kịch bản, không tự thêm nội dung.
- Không dùng cảnh giả như bằng chứng thật để nói xấu người hoặc thương hiệu có thật.

## Thứ tự bàn giao

A. Brief: thông điệp 1 câu + logline, mode, phong cách hình ảnh, style phụ đề, giọng đọc. Kèm kết quả bảng tự kiểm `references/content-quality.md`.
B. Kịch bản / transcript, kèm nguồn timing (`verified` hoặc `provisional`).
C. Bảng beat kèm lý do chọn hình ảnh.
D. Storyboard + `build/prompts.md`.
E. Asset manifest (đã có / còn thiếu).
F. `timeline.json` đã qua validate.
G. Video render và/hoặc gói CapCut, kèm ghi chú QA và các việc người dùng cần tự làm (tạo ảnh còn thiếu, duyệt giọng...).

## Chạy macro tool NHANH — BẮT BUỘC mỗi khi tạo qua Tool (không chụp màn hình giữa các bước)

Mỗi lệnh dưới đây tự làm trọn: nạp prompt → **Windows OCR tự đọc nút** ("Tạo video N" / "TẠO VIDEO KỊCH BẢN N cảnh" / "Tạo âm thanh 1" / "Tạo ảnh N") → số khớp thì tự bấm tạo → lấy kết quả. Số không khớp (đang tích dòng lạ) thì in `STOP` và KHÔNG bấm. Claude **không** chụp màn hình hay zoom kiểm nút nữa; chỉ xem ảnh trong `_macro/` khi có STOP.

| Việc | Lệnh (từ thư mục dự án) |
|---|---|
| Cảnh độc lập, Video AI (1080p, xoá logo) | `python .claude/skills/ai-semantic-video-editor/scripts/auto_tool.py video projects/<slug>/storyboard.json --collect` |
| Cảnh nối tiếp, Studio Kịch Bản | `… auto_tool.py story projects/<slug>/storyboard.json --collect` |
| Ảnh AI (`image_jobs` trong storyboard) | `… image_macro.py projects/<slug>/storyboard.json --auto --collect` |
| Giọng đọc TTS ElevenLabs | `… tts_macro.py projects/<slug>/storyboard.json --auto` (tạo + lấy file + đồng bộ luôn) |

- Lệnh `--collect` chờ lâu (vài phút): chạy nền (`run_in_background`) và làm việc khác trong lúc chờ.
- Đã nạp prompt mà bị STOP ở bước đọc nút: xử lý dòng lạ rồi chạy `--only-generate` (ảnh / Video AI / Kịch Bản qua script gốc `tao-video`), không nạp lại để tránh trùng prompt.
- Script `tao-video` (tool_macro.py, tool_story_macro.py, tool_jobs.py) chỉ được GỌI, không sửa.

## FFmpeg làm ĐẦY ĐỦ → LUÔN hậu kỳ CapCut (anh yêu cầu 08/11/2026, xem `references/capcut-post.md`)

**FFmpeg luôn làm trọn vẹn** (không bỏ trống gì): cảnh khớp giọng, sub `story_pop` (MẶC ĐỊNH: hiện từng từ đúng lúc đọc, từ đang đọc tô VÀNG `palette[2]`, mặc định #FACC15), chữ chốt `word_pop`, caption trên, **chuyển cảnh mềm** (scene `"transition_in": "fade" | "dissolve" | "smoothleft" | "fadeblack"…`, giữ nguyên thời lượng và khớp giọng). Anh đã duyệt kiểu này.

**MỌI video đều qua hậu kỳ CapCut** (kể cả video nhẹ nhàng): kiểm tra thật kỹ từng cảnh rồi thêm **hiệu ứng cảnh**, **hiệu ứng chuyển cảnh** cho đẹp và **sound effect** cho mọi hành động phát ra tiếng. Không xuất thẳng bản FFmpeg cho anh. Hiệu ứng vẫn phải hợp nội dung và cảm xúc từng cảnh (nhẹ nhàng → hiệu ứng mềm, zoom chậm, hoà tan; sôi động → rung, lóe, lia nhanh), không rải bừa. Điểm nhấn nên chọn: hình ảnh/khoảnh khắc (sản phẩm xuất hiện, cú lật, cao trào cảm xúc, trước–sau, chỗ hài), lời/chữ (hook, câu chốt, con số, giá, câu la to, CTA), âm thanh (hành động có tiếng), chuyển đoạn đổi không gian/thời gian.

Hậu kỳ CapCut: `story_render.py <sb> --capcut-layers` (cảnh + lớp chữ ĐẦY ĐỦ) → `capcut_post.py <sb>` (tắt CapCut; chuyển cảnh CapCut theo `transition_in`, bảng `sfx_cues.md` gồm SFX + các câu `capcut_text` cần hiệu ứng chữ) → mở CapCut thêm hiệu ứng lên trên (SFX tìm tiếng Anh, kéo thả đúng giây; hiệu ứng chữ / hiệu ứng cảnh Pro tại đúng câu, đúng giây) → đóng CapCut → `capcut_volumes.py <sb>` → mở lại, xuất.
Ghi điểm nhấn trong storyboard: câu chữ → `"capcut_text": [{"cue": "…", "style": "…", "why": "…"}]`; hình ảnh/khoảnh khắc → scene `"highlight": [{"at_clip": 4.0, "what": "…", "effect": "…", "why": "…"}]`; SFX → scene `"sfx"`. Tất cả vào bảng `sfx_cues.md` với đúng thời điểm trên timeline.
**Nguyên tắc:** luôn hậu kỳ; mỗi hiệu ứng / SFX phải khớp đúng hình và đúng giây, hợp cảm xúc cảnh.
**SFX khớp khung hình (bắt buộc):** mọi SFX có `at` + `end` đo bằng `sfx_frames.py` (tiếng tắt đúng lúc hành động dừng, không lố sang cảnh khác, không sót đoạn có tiếng); sau mỗi lượt sửa trong CapCut chạy `capcut_sfx_check.py`, chỉ xuất khi in `OK`. Chi tiết: `references/capcut-post.md` mục "SFX khớp từng khung hình".

## Dùng chung với skill `tao-video` (giọng kể ElevenLabs cho video nhiều cảnh)

Khi dự án có skill `tao-video` (tạo cảnh qua Tool/Muse → dựng CapCut), skill này bổ sung **giọng kể ElevenLabs đọc liền một mạch** và **sub, cảnh, graphic khớp theo giọng**. Không sửa script nào của `tao-video`.

1. Storyboard (`tao-video` Bước 3): mỗi cảnh ghi lời kể vào `"narration"` (KHÔNG ghi vào `dialogue`, để prompt tạo clip không có giọng đọc). Trong `lock` ghi "no narration, no voices, soft ambient sound only". Tuỳ chọn mỗi cảnh: `"graphic": {"template": "kinetic_text", "cue": "từ khóa trong lời kể", "hold": 3, "anchor": "center", "data": {...}}`. Tuỳ chọn cấp storyboard: `"subtitle_preset"`, `"palette"`, `"font"`.
2. Mỗi cảnh nên có lời kể đọc dài khoảng 6–10s, vừa với clip 10s. Clip ngắn hơn lời kể sẽ được làm chậm, tối đa 0.5x.
**Thứ tự:** duyệt kịch bản → tạo cảnh → lấy clip → kiểm tra clip. Giọng không phụ thuộc vào hình nên có thể tạo ngay lúc này (kể cả khi đang tạo lại cảnh lỗi), miễn là MỌI cảnh lỗi (chữ lạ, nhòe, lệch nhân vật, sai hành động) đều được TỰ SỬA hoặc tạo lại xong TRƯỚC khi dựng và xuất. Không bao giờ dựng với cảnh lỗi.
3. Lồng tiếng (sau khi duyệt kịch bản; thường làm lúc đã có clip, song song với việc sửa cảnh):
   `python .claude/skills/ai-semantic-video-editor/scripts/story_voice.py projects/<slug>/storyboard.json --voice <VOICE_ID> --speed 0.95`
   → `narration/voice.mp3`, `words.json`, `sync.json` (mốc thời gian từng cảnh). Chưa có key thì dùng `--provisional`.
   **Mặc định ở dự án này: tạo giọng bằng MACRO trên mục Giọng đọc (TTS) của tool AI VIDEO LIBRARY** (ElevenLabs có sẵn tài khoản trong tool, không cần API key). Cả quy trình khoảng 25 giây:
   0. **Chọn giọng** (`references/voice-casting.md`): anh gửi voice ID thì dùng đúng ID đó; anh nói "giọng cũ" thì để trống; anh KHÔNG đưa ID thì em TỰ CHỌN giọng hợp video bằng `voice_catalog.py search …` (ưu tiên giọng đúng ngôn ngữ, hợp vai, đã kiểm chứng). Ghi `"narration_voice": {"voice_id", "name", "auto": true, "reason", "backup"}` vào storyboard và báo giọng đã chọn kèm lý do trong bảng duyệt kịch bản.
   a. `python .claude/skills/ai-semantic-video-editor/scripts/tts_macro.py projects/<slug>/storyboard.json`: dán `voice_id` vào ô **Voice ID** và bấm **Tải giọng**, rồi đưa app lên trước, vào trang TTS, bấm "+ Thêm prompt" (dòng mới, chỉ dòng này được tích), dán toàn bộ lời kể, đóng ngăn chi tiết (~6s). Lời kể tối đa 1000 ký tự.
   b. Claude zoom vùng (1490,14)-(1568,32): nút phải ghi **"Tạo âm thanh 1"**. Ghi số khác nghĩa là đang tích thêm dòng lạ: bỏ tích dòng đó trước.
   c. `… tts_macro.py projects/<slug>/storyboard.json --only-generate`: bấm tạo, chờ file mới trong thư viện tool (khớp theo nội dung kịch bản trong `asset-state.json`, chỉ đọc), chép về `narration/voice.mp3`, rồi tự chạy `story_voice.py --voice-file` để lấy mốc từng từ bằng faster-whisper và tạo `sync.json` (~17s).
   - In ra `STOP: …` là macro đã dừng an toàn: xem ảnh `projects/<slug>/_macro/STOP_tts_*.jpg`. Hay gặp: app đang mở trình sửa workflow (bấm "Đóng" khi workflow đã lưu), có popup che (Zalo…), hoặc ngăn chi tiết đang mở.
   - Sau bước a, xem `_macro/tts_0_voice.jpg`: ô Voice ID phải đúng id và có chữ "saved". Tốc độ và Stability kế thừa từ dòng trước; muốn đổi thì chỉnh trong ngăn chi tiết trước bước b.
   - Macro chỉ bấm chuột, Ctrl+A, Ctrl+V và Esc. Không gửi phím bẫy (mục 0a trong `tao-video/references/tool.md`), không ghi file nào của tool. Lưu ý: macro ghi đè clipboard của anh.
   - Làm tay (khi macro STOP): trang TTS → "+ Thêm prompt" → dán vào ô "KỊCH BẢN PHÂN ĐOẠN" (không bấm Ctrl+Enter: phím này tạo đoạn mới) → đóng ngăn → "Tạo âm thanh 1" → lấy file `.mp3` mới nhất trong `%APPDATA%\AI_VIDEO_LIBRARY_DATAssets\` → `story_voice.py --voice-file <file>`.
   Lần thử 07/11/2026: khớp đủ 76/76 từ.
4. Có đủ clip rồi, chọn một trong hai cách:
   - **CapCut** (giữ quy trình `tao-video`): `build_capcut_draft.py --replace` → `capcut_narration.py projects/<slug>/storyboard.json` → `polish_draft.py` → xuất trong CapCut như Bước 9. Mặc định tiếng gốc của clip để 0.15; clip có sẵn giọng đọc của Muse thì dùng `--clip-volume 0`.
   - **FFmpeg, không cần CapCut**: `story_render.py projects/<slug>/storyboard.json [--preview]` → `2-xuat/<title> (giong ke).mp4`. Phụ đề dùng 6 style của skill này, có cả karaoke và pop từng từ.
5. Đổi giọng hay tốc độ đọc thì chạy lại bước 3 rồi bước 4. Cảnh, sub và graphic tự khớp lại.

Ví dụ đầy đủ cho mode 2: `examples/dao-vang/` (script, words, timeline, prompts).

## Ranh giới thực tế

Skill này tự làm được: kịch bản, timing, phụ đề, motion graphic, ghép video bằng FFmpeg, gói CapCut. Skill **không** tự tạo được ảnh/video AI trừ khi người dùng cung cấp công cụ hoặc API. Khi thiếu, xuất prompt và dùng placeholder. Không bao giờ nói video "đã xong" khi còn asset placeholder hoặc chưa render thật.
