# Hậu kỳ CapCut — LUÔN làm cho mọi video (anh yêu cầu 08/11/2026)

FFmpeg làm trọn vẹn: cảnh khớp giọng, sub hiện từng từ tô màu, chữ chốt, caption, chuyển cảnh mềm. Sau đó **MỌI video đều qua CapCut** để thêm hiệu ứng cảnh, hiệu ứng chuyển cảnh cho đẹp và sound effect. Không gửi anh bản FFmpeg thô. Trước khi làm, kiểm tra thật kỹ từng cảnh (khung hình thật, đúng lời, không lỗi).

Chọn chỗ thêm theo nội dung từng video, ví dụ:
- **Hình ảnh / khoảnh khắc**: lúc sản phẩm xuất hiện lần đầu (hero shot), cú lật / twist, sự thật lộ ra, cao trào cảm xúc, khoảnh khắc nhận ra, cảnh trước–sau, chỗ gây cười, chuyển giai đoạn câu chuyện.
- **Lời / chữ**: câu chốt, bài học, câu hỏi mở đầu (hook), con số hay thông tin quan trọng, giá / khuyến mãi, câu la to, CTA.
- **Âm thanh**: MỌI hành động phát ra tiếng (→ SFX), nhịp cần dồn dập hoặc lặng đi.
- **Chuyển đoạn**: mỗi chỗ đổi không gian / thời gian có chuyển cảnh CapCut đẹp.
Hiệu ứng chọn hợp nội dung và cảm xúc (rung + lóe cho sốc, zoom chậm + mờ viền cho cảm động, glitch cho bất ngờ, sticker/hiệu ứng vui cho hài, hoà tan/mờ cho video nhẹ nhàng…). Lớp chữ FFmpeg KHÔNG bỏ trống; CapCut thêm lên trên.

## Chia việc
| Phần | Làm bằng |
|---|---|
| Cảnh khớp giọng, sub từng từ, chữ chốt, caption (đầy đủ) | **FFmpeg + code**: `story_render.py --capcut-layers` → `segments/seg_*.mp4` + `text_layer.mov` |
| Ghép cảnh + lớp chữ + giọng, chuyển cảnh CapCut, bảng cue | **Script** `capcut_post.py` (CapCut TẮT) |
| SFX, hiệu ứng chữ tại câu `capcut_text`, hiệu ứng cảnh, chuyển cảnh Pro | **CapCut** (giao diện) theo `narration/sfx_cues.md` |
| Âm lượng | **Script** `capcut_volumes.py` (CapCut TẮT) |
| Xuất | **CapCut** → chép `%LOCALAPPDATA%\CapCut\Videos\` → `projects/<slug>/2-xuat/` |

## Nguyên tắc: luôn thêm, nhưng đúng chỗ đúng giây
**SFX**: chỉ khi trên hình có **hành động phát ra tiếng** mà video **chưa có tiếng đó** (clip AI đã tắt tiếng gốc).
- Thêm: điện thoại reo/rung, vỡ bát, mở/đóng cửa, gõ phím, gập laptop, đặt bát đĩa, đồng hồ tích tắc khi đồng hồ được quay cận, bước chân chạy, gió/mưa khi thấy rõ, sấm khi có chớp.
- Không thêm: hành động im lặng, cảnh không có nguồn âm, để lấp chỗ trống. Hai tiếng cùng loại cách nhau < 2s → giữ một. SFX luôn nhỏ hơn giọng.
- Khoảng 1 SFX mỗi 5–8 giây; khớp khung hình hành động (lệch ≤ ~0.2s).

**Chuyển cảnh**: chỉ ở chỗ **đổi không gian/thời gian**; cùng bối cảnh → cắt thẳng. Lắng → hòa tan/mờ; gấp → lia/zoom; khoảnh khắc nhận ra → lóe sáng.

**Hiệu ứng cảnh / chữ nâng cao**: chỉ ở khoảnh khắc cần nhấn (hook, bước ngoặt, câu chốt, bài học). Không rải đều.

## ⏱ SFX KHỚP TỪNG KHUNG HÌNH — BẮT BUỘC (anh yêu cầu 09/11/2026)
Lỗi anh đã bắt: gõ phím vẫn kêu khi đã đặt điện thoại xuống, tiếng cãi còn kêu khi đã hết cãi, gió kêu lố sang cảnh khác, đoạn đang cãi lại không có tiếng. Vì vậy:
1. **Mọi SFX có cả mốc BẮT ĐẦU và mốc KẾT THÚC**, đo trên khung hình thật, không ước lượng theo prompt hay `beats`:
   `python scripts/sfx_frames.py projects/<slug>/storyboard.json` → `narration/build/sfx_frames/scene_XX.jpg` (4 khung/giây, góc ô ghi giây timeline). Xem từng ảnh, ghi `sfx[i].at` = giây hành động bắt đầu, `sfx[i].end` = giây hành động kết thúc (giây timeline). Hành động kéo dài qua cảnh sau (đi bộ liền 2 cảnh) thì thêm `"cross_scene": true`; nếu không, `capcut_post.py` tự cắt SFX ở cuối cảnh và báo.
2. **Không bỏ sót hành động có tiếng**: rà ảnh từng cảnh, chỗ nào nhân vật há miệng cãi/quát, gõ, đi, vật rơi, chim bay… đều phải có SFX. Một hành động lặp ở nhiều cảnh (cãi ở 4 chỗ) thì 4 clip SFX riêng, mỗi clip đúng đoạn của nó.
3. Sau khi thêm/sửa trong CapCut, **chạy `python scripts/capcut_sfx_check.py projects/<slug>/storyboard.json` sau MỖI lượt thao tác** (CapCut đang mở vẫn chạy được, vì CapCut tự lưu `draft_content.json`). Script in vị trí thật của từng SFX, so với kế hoạch (lệch > ±0,15s là ✗), báo SFX chưa hạ âm lượng, và báo nếu **track video chính bị mất/xê dịch cảnh**. Chỉ xuất khi script in `OK`.

### Thao tác SFX trong CapCut cho chính xác (bài học 09/11/2026)
- **Thả từ thư viện** vào timeline tại x = 84 + giây × px/giây là cách đặt điểm bắt đầu chuẩn nhất (sai ±0,05s). **Kéo dịch clip một đoạn nhỏ (< 1s) KHÔNG ăn**: CapCut bắt dính về chỗ cũ. Muốn đổi điểm bắt đầu thì xoá clip rồi thả lại đúng giây.
- Cắt đuôi: chọn clip → bấm thước tại giây kết thúc → `ctrl+b` → `BackSpace`. Thước hay **bắt dính** vào mép gần nhất (mép cảnh, mép sub): bấm lệch 2–3px về phía cần, rồi kiểm bằng `capcut_sfx_check.py`.
- ⚠️ **Không bấm `ctrl+b` / `BackSpace` khi chưa chắc clip SFX đang được chọn**: nếu không có clip nào được chọn, `ctrl+b` cắt TRACK VIDEO CHÍNH và `BackSpace` xoá luôn một cảnh (các cảnh sau tự dồn lên). Gặp thì bấm **nút Hoàn tác trên thanh công cụ timeline** (~(59,357) khi cửa sổ phóng to). `ctrl+z` có thể không ăn vì CapCut báo "phím tắt xung đột".
- Khi thả SFX đè lên clip khác, CapCut tạo hàng mới bên dưới (y khác). Đặt âm lượng ngay sau khi thả, lúc clip vừa thả còn đang được chọn: kéo nút tròn âm lượng bằng `left_mouse_down` → `mouse_move` từng bước → `left_mouse_up` (`left_click_drag` không ăn).
- Ô tìm SFX: bấm ô → `End` → `BackSpace` ×25 → gõ. `shift+Home` không chọn được chữ cũ (sẽ thành "windtyping").
- Hiệu ứng hình kéo vào khoảng trống trên track chữ (y ≈ 443) sẽ tạo track hiệu ứng. Hiệu ứng zoom áp lên cả lớp sub, nên giữ ≤ 1,5s.

## Storyboard
```jsonc
"capcut_text": [{"cue": "chỉ còn 99k", "style": "chữ to rung + lóe sáng", "why": "giá sốc"}],  // câu cần hiệu ứng chữ CapCut (chỉnh thêm lên trên)
"scenes": [{ …,
  "transition_in": "Phóng to rồi mờ dần",           // tên CapCut (route CapCut) hoặc xfade FFmpeg ("fade", "dissolve"…); tên CapCut khi render FFmpeg = "fade"
  "sfx": [ {"at": 12.40, "end": 13.55, "sound": "điện thoại rung", "search": "phone vibrate", "volume": 0.45,
            "why": "điện thoại sáng và rung trên bàn"} ],   // at/end = giây TIMELINE đo bằng sfx_frames.py (hoặc at_clip/end_clip = giây trong clip)
  "effect": {"name": "Rung", "at_clip": 6.0, "dur": 0.8, "why": "khoảnh khắc nhận ra"},
  "highlight": [ {"at_clip": 4.0, "what": "hình: hai mẹ con ôm nhau", "effect": "zoom chậm + vignette + lóe sáng nhẹ",
                  "why": "cao trào cảm xúc"} ]   // điểm nhấn bất kỳ (hình, khoảnh khắc, câu…), tự chọn theo nội dung
}]
```
- `search` viết **tiếng Anh** (thư viện SFX CapCut gần như toàn tên tiếng Anh; tìm tiếng Việt ra kết quả sai).
- `volume` tuyến tính: SFX nhẹ 0.25–0.35 (gõ phím, đặt bát), vừa 0.4–0.45 (điện thoại, cửa, gập laptop). Giọng kể 1.6.

## Thao tác trong CapCut (đã chạy thật 08/11/2026, CapCut 9.7.1, cửa sổ phóng to 3440×1440)
1. Mở project "<title> (hau ky)" ở trang chủ (ô đầu danh sách). Phóng to cửa sổ.
2. Tab **Âm thanh** (56,25) → mục trái dưới cùng **Hiệu ứng âm thanh** (25,338).
3. Mỗi SFX: bấm ô tìm (250,46) **hai lần** (lần đầu chỉ bỏ focus khỏi ô khác — nếu không Ctrl+A sẽ chọn hết timeline) → Ctrl+A → gõ `search` → Enter → chờ ~8s → zoom danh sách, chọn kết quả hợp (ưu tiên độ dài vừa hành động) → bấm nút tải (523, y dòng) → **kéo thả** dòng đó xuống timeline tại x = 84 + giây × 10.6, vào hàng trống dưới track giọng (y≈556 / 588).
4. **Không gõ âm lượng trong giao diện** (không ăn / có khi thành +11 dB). Âm lượng đặt bằng `capcut_volumes.py` sau khi đóng CapCut.
5. Bấm vào vùng trống timeline để bỏ chọn trước khi làm SFX kế tiếp.
6. Đóng project (CapCut lưu) → đóng CapCut → `capcut_volumes.py <sb>` → mở lại CapCut, mở project → Ctrl+E → Xuất → hộp mời chia sẻ bấm **Đóng** (không chia sẻ).
7. Kiểm tra: đoạn chỉ có giọng ≈ −9 dB đỉnh, đoạn có SFX không vượt ≈ −3 dB (`ffmpeg -af volumedetect` theo từng khoảng).

## Bài học lần chạy 08/11/2026 ("Dậy sớm hay thức khuya", cửa sổ 1568×656 sau phóng to)
- Timeline mặc định: x = 84 + giây × 8.55 (tính từ đuôi track giọng; mỗi lần mở có thể khác → đo lại bằng mép cuối track giọng).
- Ô tìm: KHÔNG dùng Ctrl+A (nếu focus ở timeline sẽ chọn hết và các phím gõ thành phím tắt). Cách đúng: bấm ô (250,46) → `End` → `shift+Home` → gõ. Gõ chuỗi có dấu cách bị chuyển qua clipboard và dán nhầm nội dung cũ → dùng 1 từ tiếng Anh (footsteps, vibration, whoosh, door, keyboard, birds, switch, yawn, curtain).
- Nút bên phải dòng SFX: mũi tên = tải; khi đã tải nó thành "+" và bấm vào sẽ CHÈN clip vào cuối track ở đầu phát → đừng bấm, chỉ cần kéo thả (kéo tự tải).
- Xoá clip: chọn rồi `BackSpace` (phím Delete không ăn). Cắt ngắn SFX/hiệu ứng: bấm thước thời gian tại giây cần cắt → chọn clip → `ctrl+b` → chọn phần thừa → `BackSpace`. Đừng kéo mép phải (dễ dính nút làm mờ dần).
- Ô tìm hiệu ứng hình có thể lỗi mạng ("Đang tải…" mãi) → chọn theo danh mục (dropdown "Hiệu ứng video": Chuyển động có "Rung lắc", Làm mờ…).
- Hiệu ứng hình trên track hiệu ứng áp lên CẢ lớp chữ: hiệu ứng mờ/biến dạng mạnh sẽ che phụ đề → chỉ dùng hiệu ứng ngắn (≤1s) kiểu rung/lóe, tránh làm mờ khi đang có sub.
- Cửa sổ CapCut có thể bị thu nhỏ/ẩn sau khi mở: khôi phục bằng ShowWindow(MainWindowHandle, 3); cấp quyền computer use cho cả "CapCut" và "capcut.exe".
- (08/11 tối) Bấm vào clip là ĐẦU PHÁT NHẢY tới chỗ bấm. Cắt đúng giây: chọn clip TRƯỚC → bấm thước thời gian (y≈370) tại giây cần cắt → `ctrl+b` → phần bên phải đang được chọn → `BackSpace`. Cắt sai thì `ctrl+z`.
- File SFX dài (vài phút) kéo thả hay không ăn: đặt đầu phát (bấm thước) rồi bấm nút "+" của dòng đó để chèn đúng chỗ, sau đó cắt đuôi theo cách trên.
- Thả SFX vào hàng trống CHƯA có track (dưới track cuối) thì bị bỏ qua: thả vào hàng SFX đã có (y≈562) — CapCut tự tạo hàng mới nếu chồng lấn.
- Đóng CapCut bằng nút X (2 lần: project → trang chủ → thoát), chờ hết tiến trình (~30s). KHÔNG `taskkill /F` (từng làm mất đăng nhập). Mở lại có thể hiện bảng quảng cáo Pro: đóng bằng X góc trên phải, không bấm "Dùng ngay/Mua".
- Thay hình project hậu kỳ mà GIỮ SFX: ghi đè các file `narration/build/final/segments/seg_*.mp4` (cùng thời lượng) khi CapCut đã tắt.
- (08/11 khuya) CapCut của anh TỰ ĐĂNG XUẤT mỗi khi thoát hẳn (kể cả đóng bằng X) → hạn chế tắt CapCut: chỉ tắt 1 lần để tạo project (compose/capcut_post), còn ÂM LƯỢNG SFX chỉnh NGAY trong CapCut: chọn clip → panel phải "Âm lượng", kéo nút tròn từ x≈1395 (0 dB) sang trái: x≈1340 ≈ −10 dB (SFX), x≈1310 ≈ −16 dB (nền đám đông). Không cần capcut_volumes.py.
- Trước khi bấm vào CapCut luôn đưa cửa sổ CapCut lên trước (ShowWindow + SetForegroundWindow) — có lần AI VIDEO LIBRARY nằm trên và nhận nhầm cú bấm.
