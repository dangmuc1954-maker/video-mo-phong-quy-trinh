---
name: video-mo-phong-quy-trinh
description: >-
  Làm video KỂ CHUYỆN PHÂN TÍCH KIẾN TRÚC / CÔNG TRÌNH bằng hoạt hình MÔ PHỎNG KỸ THUẬT 3D, kể nhập vai ngôi thứ hai, kiểu trend "Chúc mừng bạn đã phát minh ra cầu Lư Câu": mở bằng bài toán gốc hoặc "xé toạc" công trình, rồi đi đúng trình tự xây thật, mỗi bước lộ khuyết điểm và "bạn" nghĩ ra cách giải, kết "Xin chúc mừng bạn, bạn đã xây thành công …" + hình thật. Hình có chiều sâu (mặt cắt, nhìn xuyên, bung rời, mũi tên lực) khớp lời kể từng giây; tạo cảnh qua Studio Kịch Bản của tool AI VIDEO LIBRARY, giọng ElevenLabs, sub story_pop, hậu kỳ CapCut. Dùng khi anh nói: "video kiến trúc", "video phân tích công trình", "chúc mừng bạn đã phát minh/xây…", "mô phỏng quá trình xây …" (kim tự tháp, Vạn Lý Trường Thành, cầu, đập, lâu đài, tháp…), hoặc video mẫu (video-theo-mau) thuộc dạng này. KHÔNG dùng cho video tài liệu graphic số liệu/bản đồ (→ video-tai-lieu) hay hoạt hình kể chuyện nhân vật (→ tao-video).
---

# Video mô phỏng quy trình xây dựng — kể nhập vai "Chúc mừng bạn…"

Đọc file này từ đầu đến cuối, rồi đọc 2 tài liệu bắt buộc trước khi viết bất cứ gì:
1. [references/kich-ban.md](references/kich-ban.md) — cách viết kịch bản (mở đầu, thân bài, câu dẫn ngắn, câu chốt) + **kịch bản mẫu Kim tự tháp** (chuẩn vàng).
2. [references/hinh-mo-phong.md](references/hinh-mo-phong.md) — phong cách hình mô phỏng 3D, bộ hiệu ứng chiều sâu, cách viết prompt theo giây.
Tham khảo: [references/phan-tich-mau.md](references/phan-tich-mau.md) — video mẫu được dựng thế nào (bảng theo giây).

```
S=.claude/skills/tao-video/scripts   A=.claude/skills/ai-semantic-video-editor/scripts   M=.claude/skills/video-mo-phong-quy-trinh/scripts
projects/<slug>/ build_sb.py → storyboard.json · facts.json · narration/ · 1-canh/ · 2-xuat/
```
Chạy từ thư mục dự án gốc, luôn `export PYTHONIOENCODING=utf-8`. Lệnh lâu → `run_in_background`.

## LUẬT VÀNG (anh đã chốt 11/11/2026 — vi phạm là làm lại)
| # | Luật | ✅ Đúng | ❌ Sai |
|---|---|---|---|
| 1 | **Hình là MÔ PHỎNG KỸ THUẬT 3D** | mô hình CGI sạch, vật tự lắp vào chỗ, mặt cắt, mũi tên lực | "photorealistic", "cinematic", cảnh drone quay công trình đã xong |
| 2 | **Có chiều sâu mỗi cảnh** | ≥2 lớp: mặt cắt, nhìn xuyên, bóc lớp, bung rời, máy chui vào trong, zoom vĩ mô→vi mô… | hình phẳng, chỉ nhìn bề ngoài |
| 3 | **Một quá trình xuyên suốt** | cùng một công trường, công trình lớn dần, đúng trình tự thi công thật | các "mẹo" rời rạc, nhảy bối cảnh lung tung |
| 4 | **Mở đầu có vấn đề** | Kiểu A "bài toán gốc" (vì sao phải xây) hoặc Kiểu B "xé toạc" rồi chỉ về những viên đá đầu tiên | mở bằng "Chúc mừng bạn!" trống rỗng |
| 5 | **Mỗi bước: làm → khuyết điểm → bạn giải** | khuyết điểm có thật, diễn bằng hình rồi mới giải | bước nào cũng chỉ kể "bạn làm A, rồi B" |
| 6 | **Không đọc "giai đoạn 1, 2…"** | "Việc đầu tiên là…", "Tiếp theo là…", "Rồi đến…", "Cuối cùng là…" | "Giai đoạn một: nền móng" |
| 7 | **"Người khôn như bạn" ≤ 2 lần**, còn lại câu dẫn NGẮN xoay vòng | "Nhưng bạn không chịu bỏ cuộc." · "Ngàn cân treo sợi tóc, bạn lại sáng lên ý tưởng." | lặp một câu khen 5 lần |
| 8 | **Hình khớp lời từng giây** | storyboard ghi `beats` theo giây, mỗi nhịp = một cụm lời | một câu action chung cho 10 giây |
| 9 | **Đúng kiến thức** | số liệu có nguồn (`facts.json`), giả thuyết nói rõ "người ta cho rằng" | bịa kỹ thuật, bịa số |
| 10 | **Kết** | "Xin chúc mừng bạn, bạn đã xây thành công <tên> !" + cảnh cuối là ẢNH/VIDEO THẬT của công trình | kết bằng hình AI |
| 11 | Chữ lớn đặt tên kỹ thuật **2–3 lần/video**; sub `story_pop` vàng | đặt tên đúng lúc "Bạn gọi chúng là…" | chữ nhấn mọi câu |
| 12 | **Chưa xây thì không được thấy** (trạng thái xây dựng) | mỗi cảnh có `da_co` / `chua_co`; tên công trình không nằm trong style/settings; cảnh 1 mặt đất trống có ảnh khung đầu | công trình hoàn chỉnh xuất hiện khi lời kể mới nói đo đường, đào móng |

## LUẬT LIỀN MẠCH CHO MACRO (anh yêu cầu 13/11/2026: "nạp xong là bấm tạo liền, đừng sững lại")
- **Nạp xong là bấm tạo NGAY.** Không đặt bước kiểm nào chặn trước nút tạo (OCR số trên nút từng mất 23s và hay đọc hỏng — chính là chỗ sững). Dự án Studio Kịch Bản mới chỉ có cảnh của mình nên không cần kiểm; kiểm SAU khi bấm bằng hàng đợi (`tool_jobs.py status`: đủ cảnh, model `omni-flash-1.1`).
- Mọi bước chờ phải **đo, không đoán**: `python $A/profile_macro.py projects/<slug>/storyboard_tool.json` (chỉ nạp, không bấm tạo) in bảng bước nào mất ≥0.6s. Mục tiêu: nạp + gắn ảnh + bấm tạo ≤ ~10s. Mốc đo 13/11: bản cũ 24s nạp (20s là chờ cố định sau mỗi cú bấm) + 23s OCR + 8s chờ sau khi bấm.
- Chờ theo trạng thái, không chờ cứng: sau khi bấm tạo thoát ngay khi Cảnh 1 vào hàng đợi (hỏi mỗi 0.8s).
- Thêm bước kiểm mới vào macro → chạy `profile_macro.py` trước; bước nào làm chậm > 2s phải chuyển ra SAU khi bấm hoặc chạy nền.

## LUẬT KHÔNG NGHỈ (anh yêu cầu 13/11/2026: "mỗi giây em chạy đều tốn tiền của anh")
- Không dừng hỏi / chờ giữa các bước đã có trong quy trình. Chỉ dừng khi THẬT SỰ không còn việc nào khác làm được.
- Hễ một việc chờ (tool tạo cảnh ~1–3 phút/cảnh): chạy nền (`run_in_background`) rồi LÀM NGAY việc độc lập khác: giọng kể, `sfx_synth.py`, ảnh thật, soát kịch bản, viết kế hoạch hậu kỳ, kiểm cảnh đã về, xoá logo cảnh vừa về.
- Chỉ MỘT macro điều khiển giao diện tại một thời điểm (một chuột): xếp hàng nối đuôi nhau, không chờ cách quãng.
- Nối lệnh: mỗi cảnh về là xử lý luôn (xoá logo → kiểm); đủ cảnh là dựng ngay; dựng xong là hậu kỳ và giao AI soát song song với xuất CapCut.
- Việc nằm trong quyền anh đã cấp (tool của anh, CapCut) làm luôn, không xin phép lại. Chỉ hỏi khi việc có thể xoá/đè dữ liệu của anh.

## 10 bước (mỗi bước có cổng qua)

### 1. Chọn công trình + bài toán gốc
Viết 5 dòng vào đầu `build_sb.py`: **công trình**, **ai cần & vì sao** (hoặc ghi "dùng xé toạc"), **mục tiêu**, **thử thách** (địa hình, thời tiết, vật liệu, kẻ thù…), **câu chốt** (thành tựu thật). Mọi khuyết điểm phía sau phải sinh ra từ các thử thách này.

### 2. Nghiên cứu quy trình xây THẬT → `facts.json`
WebSearch / web-fetch (ưu tiên en.wikipedia, bảo tàng, đại học, báo khoa học). Ghi: trình tự công đoạn đúng thứ tự, kỹ thuật thật ở từng bước, số liệu (kích thước, năm, số khối…) kèm `source`/`url`. Chỗ giới khoa học còn tranh cãi → ghi `"hypothesis": true` (lời kể phải nói "người ta cho rằng").
Cổng: ≥8 công đoạn có nguồn; mỗi công đoạn có ≥1 khó khăn thật.

### 3. Kịch bản (theo `references/kich-ban.md`)
12–16 cảnh, tổng 2–2,5 phút; mỗi cảnh 8–12s lời (26–36 âm tiết). Tự kiểm bảng 8 điểm cuối `kich-ban.md`.

### 4. Kịch bản hình + storyboard (theo `references/hinh-mo-phong.md`)
Copy [templates/kim-tu-thap.build_sb.py](templates/kim-tu-thap.build_sb.py) thành `projects/<slug>/build_sb.py`, sửa nội dung. Mỗi cảnh: `narration`, `beats` (mốc giây ↔ cụm lời ↔ hình + ≤2 hiệu ứng chiều sâu), `camera`, `graphic` (chỉ ở cảnh đặt tên), **`da_co` + `chua_co`** (luật 12: đã xây tới đâu / chưa xây gì — chi tiết `hinh-mo-phong.md` mục 7), cờ `hoan_thanh` / `tua_lai`. Gốc storyboard có `ten_cong_trinh` (tên tiếng Anh, chữ thường) và bối cảnh `settings.site` KHÔNG chứa tên công trình. Cảnh cuối `"real_photo": "File:…"` (tìm bằng `python .claude/skills/video-tai-lieu/scripts/find_photo.py "<tên công trình>" --out projects/<slug>/render/_find.jpg`, Read ảnh rồi chọn).
```
python projects/<slug>/build_sb.py && python $M/prep.py projects/<slug>/storyboard.json
```
`prep.py` tự soát luật vàng (chữ 'photorealistic', 'giai đoạn', lặp câu dẫn, thiếu beats/chiều sâu, cảnh quá dài, thiếu ảnh thật…) rồi sinh prompt + `storyboard_tool.json` (bỏ cảnh ảnh thật). Cổng: in `OK`.
🛑 Gửi anh bảng duyệt: bài toán gốc (1 dòng) · bảng `# | lời kể | hình mô phỏng (theo giây) | chữ lớn`. Anh nói "làm luôn" thì bỏ qua.

### 5. Tạo cảnh (Studio Kịch Bản, nối khung cuối)
⚠️ Chỉ **Omni 1.1 Flash** (Omni 1.2 Flash đốt credit gấp 3 lần): sau khi nạp, Read `_macro/1_canh1.jpg` kiểm ô model trước khi bấm tạo; sau khi tạo `tool_jobs.py status` phải ghi `omni-flash-1.1`.
Kiểu A (cảnh 1 mặt đất trống): tạo ảnh khung đầu trước (`image_jobs` + `$A/image_macro.py … --auto --collect`, xem `hinh-mo-phong.md` mục 7.5) rồi chạy `prep.py` lại.
```
python $A/fast_tool.py projects/<slug>/storyboard_tool.json      # MỘT mạch: nạp prompt → gắn ảnh → kiểm nút → bấm tạo (~35s), chờ co 0.55, OCR nhiều biến thể
```
(`auto_tool.py story …` cũ vẫn dùng được nhưng 3 tiến trình + chờ cố định, chậm hơn.)
- In `OCR nút: '…' → KHÔNG KHỚP` → Read `projects/<slug>/_macro/ocr_button.png`; nếu ghi đúng "TẠO VIDEO KỊCH BẢN N cảnh" (OCR hay đọc sai chữ) thì chạy `python $S/tool_story_macro.py projects/<slug>/storyboard_tool.json --only-generate`.
- `STOP: … 'mo_trang_kich_ban' … 'other'` → tool đang mở trình sửa workflow: Read ảnh STOP, nếu góc phải ghi "Đã lưu" thì bấm "Đóng" (`python -c "import sys;sys.path.insert(0,'$S');import tool_macro as T;T.focus_app(True);T.click(1491,24,2)"`) rồi chạy lại. Hộp thoại lạ → `T.key(0x1B)` (Esc).
- Lấy clip (nền): `python $S/tool_jobs.py collect projects/<slug>/storyboard_tool.json --wait 3600`. 16 cảnh nối tiếp ≈ 40 phút.
- Cảnh cuối là ảnh thật: không tạo trong tool — `python $M/photo_clip.py projects/<slug>/storyboard.json` (tải ảnh, làm clip zoom chậm).

### 6. Giọng kể (song song lúc chờ cảnh)
```
python $M/tts_parts.py projects/<slug>/storyboard.json
```
Tự chia lời kể thành ≤3 phần ≤990 ký tự theo ranh giới cảnh, tạo từng phần qua macro TTS, KIỂM độ dài từng phần, ghép, đồng bộ (`sync.json`). In `STOP` thì đọc lý do, sửa rồi chạy lại đúng phần lỗi: `--only-part 1`.

### 7. Kiểm cảnh
```
python $S/analyze_clips.py projects/<slug>/storyboard.json
```
Read `1-canh/_review.jpg`: cảnh có đúng hình mô phỏng như `beats` không, có chiều sâu không, có chữ lạ/logo không, **và đối chiếu `da_co` / `chua_co` từng cảnh: có thấy phần chưa xây (nhất là tường/tháp xong sớm ở cảnh đầu) không**. Nhảy hình giữa clip → tăng `trim_start` trong `edit_plan.json`. Logo Gemini (ngôi sao góc phải dưới, clip 720×1280) → `python $M/photo_clip.py … --delogo` (xoá cho mọi clip, giữ bản gốc trong `1-canh/_goc/`). Cảnh sai nội dung → tạo lại cảnh đó trong Video AI với ảnh khung cuối cảnh trước (tối đa 2 lần).

### 8. Dựng
```
python $A/story_render.py projects/<slug>/storyboard.json            # bản FFmpeg đầy đủ (giọng, sub story_pop, chữ lớn)
python $M/sfx_synth.py                                                # (1 lần) tạo bộ âm thanh: mưa, gió, sấm, dế, chim, whoosh, swish, lấp lánh, ding, chime, nhịp tim…
python $M/post_capcut.py projects/<slug>                              # hậu kỳ ĐẦY ĐỦ: chuyển cảnh CapCut mỗi ranh giới đổi bối cảnh + SFX mọi hành động + ambient từng cảnh + nhạc dịu (CapCut TẮT; chỉ thêm --force khi CapCut ở màn hình chính, không mở dự án)
```

### 9. Kiểm cuối độc lập
`python $M/review_frames.py projects/<slug>` (KHÔNG dùng review_sheet.py của video-tai-lieu — ra tờ đỏ với video này) → giao một agent MỚI soát theo mục "Kiểm cuối" trong `references/kich-ban.md` (+ luật vàng ở trên). Chỉ đi tiếp khi `KẾT LUẬN: ĐẠT`.

### 10. Xuất + gửi
Mở CapCut → project `<title> (hau ky)` → Xuất → Xuất (1080p). Chặn đỉnh âm:
`ffmpeg -i "<file xuất trong Downloads>" -c:v copy -af "alimiter=limit=0.89:level=disabled" -c:a aac -b:a 256k "projects/<slug>/2-xuat/<title>.mp4"` → SendUserFile + 3 dòng: bài toán gốc, công đoạn chính, nguồn. Không tắt CapCut; dọn file tạm chỉ khi anh OK.

## Lỗi hay gặp
| Hiện tượng | Cách xử lý |
|---|---|
| Công trình xong ngay cảnh đầu | `style`/`settings` còn tên công trình, hoặc thiếu `chua_co`/ảnh khung đầu → sửa theo luật 12 rồi tạo lại từ cảnh đầu |
| Cảnh ra giống phim quay thật | prompt còn chữ "photorealistic / cinematic / drone" → bỏ; thêm câu cấm trong `negative` (xem hinh-mo-phong.md) |
| Tổng thời lượng sync bất thường (vd 600s) | một phần TTS chép nhầm file cũ → `tts_parts.py` tự chặn; chạy lại `--only-part N` |
| Lời kể > 12s/cảnh | clip 10s bị làm chậm < 0.8x → rút lời hoặc tách cảnh |
| Cảnh có mảng xám phẳng (mặt cắt render lỗi) | cắt bỏ vùng xám + phóng lại: `ffmpeg -i 1-canh/_goc/scene_NN.mp4 -vf "crop=iw*0.70:ih*0.70:iw*0.08:0,scale=720:1280" …`; hoặc tạo lại cảnh. Khi xem `_review.jpg` ở bước 7 phải soi từng cảnh có "section/cutaway" |
| Công trình đã xong ngay từ cảnh 1–5 dù lời kể mới đo đường/đào móng | tool hay vẽ sẵn tường hoàn chỉnh. Prompt cảnh đầu ghi rõ "bare empty ridge, NO wall yet" và tả hình sẽ có; chấp nhận nếu cảnh sau đã khớp lời |
| Chữ lớn lố sang đầu cảnh kế | `tts_parts.py` tự chỉnh `hold`; chạy lại riêng: `tts_parts.py <sb> --clamp-only` rồi dựng lại |
| Tool nằm đè CapCut khi mở CapCut để xuất | macro đặt tool "luôn trên cùng": thu nhỏ cửa sổ tool (`T.focus_app(False); T.u32.ShowWindow(T.HWND, 6)`) rồi mở CapCut |
| Macro dừng vì tool đang ở trang khác |
| Macro dừng vì tool đang ở trang khác | xem mục 5; không chụp màn hình thủ công |

## Chạy song song nhiều chuỗi cảnh (đã thử 13/11/2026, video đạo lý ốc sên)
- Mỗi chuỗi = một dự án Studio Kịch Bản riêng. `split_chains.py` (trong projects/dao-ly-oc-sen) chia storyboard theo trường `chain` ("A"/"B"…), mỗi chuỗi có ảnh tham chiếu ở cảnh đầu để giữ nhân vật.
- **Thứ tự bắt buộc:** nạp TẤT CẢ chuỗi trước (A → B → …), RỒI mới bấm "Tạo video" từng dự án. Nếu bấm tạo A trước khi nạp B thì macro không tạo được dự án B riêng (nó nạp B chung vào dự án A đang chạy; dự án 8 cảnh tự chạy tiếp thành một chuỗi dài, không song song). Sau đó đừng bấm tạo ở dự án B thừa (trùng quota).
- Macro nạp ảnh tham chiếu giờ kiểm hộp chọn file (`file_dialog_open`) và tự thử nhiều vị trí ô "+" (bố cục lệch y 162–175); không mở được thì dừng, không gõ đường dẫn vào ô prompt.
- Giọng kể ≤ 1000 ký tự chạy một lượt ngay khi có storyboard (không phụ thuộc cảnh).

## Bài học 13/11/2026 (đã chạy thử trọn vẹn: video đạo lý "Ốc sên leo cây" 70s, 16 phút từ lúc giao việc tới lúc dựng xong)
**Tốc độ — việc nào làm song song được:** AI biên kịch (45s) ‖ AI nhân vật/ảnh khung đầu (1 phút) → nạp tool → giọng kể chạy trong lúc cảnh đang tạo → mỗi cảnh về là xoá logo → đủ cảnh dựng FFmpeg → hậu kỳ → AI soát ‖ xuất CapCut. Mẫu giao việc: `references/giao-viec-ai-phu.md`.
**Một chuột:** chỉ MỘT macro điều khiển giao diện tại một thời điểm → xếp nối đuôi, không cách quãng. Chia 2 chuỗi cảnh chạy song song trong tool: nạp hết các chuỗi (`split_chains.py` → storyboard_A.json, storyboard_B.json) RỒI mới bấm tạo; nếu bấm tạo A trước thì B bị nối vào A.
**Công cụ nhanh:** `fast_tool.py` (một tiến trình, chờ co 0.55, OCR nhiều biến thể — hết dừng vì đọc sai số trên nút; nút xanh chữ trắng đọc bằng ngưỡng sáng). Macro gắn ảnh kiểm hộp chọn file Windows đã mở (không mở = dừng, không gõ đường dẫn vào ô prompt) và thử nhiều vị trí ô "+".
**Model:** chỉ Omni 1.1 Flash (1.2 đốt credit gấp ~3 lần). Kiểm `tool_jobs.py status` phải ghi `omni-flash-1.1`.
**Cảnh sửa lẻ:** muốn tạo lại 1 cảnh giữa chuỗi → storyboard 1 cảnh (`reference_images` = khung cuối cảnh trước, trích bằng ffmpeg), chạy `fast_tool.py`; XOÁ `1-canh/scene_NN.mp4` cũ trước khi `tool_jobs.py collect` (collect bỏ qua file đã có) và xoá `1-canh/_goc/scene_NN.mp4` trước khi `photo_clip.py --delogo`.
**Hậu kỳ CapCut:** `sfx_synth.py` (1 lần) → `post_capcut.py` (mỗi ranh giới đổi bối cảnh có chuyển cảnh; 40+ âm thanh/video 70s: ambient từng cảnh, mưa/gió/sấm, bò/leo, nhịp tim, lấp lánh, ding, whoosh/swish, chime mở/chốt, nhạc pad). Dự án đang mở trong CapCut bị khoá → dựng tên mới `--title "<tên> v2 (hau ky)"`; CapCut chỉ thấy draft mới sau khi về Trang chủ (Menu ở góc trái trên → "Quay lại trang chủ").
**CapCut Pro (anh cho phép dùng chuyển cảnh Pro, 13/11/2026):** skill dùng mọi chuyển cảnh có sẵn (kể cả "Quét tro"…), KHÔNG chặn. Nếu nút xuất đổi thành **"Mua gói Pro để xuất video"** thì thường là CapCut CHƯA ĐĂNG NHẬP gói Pro của anh (13/11/2026 chính là lý do này): em KHÔNG bấm mua/dùng thử — nhắn anh đăng nhập CapCut Pro rồi xuất ngay, không dựng lại. Trước khi dựng/xuất video mới, nhắc một câu "CapCut đã đăng nhập Pro chưa anh?" nếu chưa thấy huy hiệu Pro. Trước khi bấm xuất vẫn zoom nút: ghi "Xuất" mới bấm.
**Mở CapCut khi tool đang nằm trên cùng:** thu nhỏ cửa sổ tool trước (`T.focus_app(False); T.u32.ShowWindow(T.HWND, 6)`) rồi `open_application CapCut`.
**Soát cuối:** `review_frames.py` + AI soát Sonnet; đừng dùng `review_sheet.py` của video-tài-liệu cho video này.
