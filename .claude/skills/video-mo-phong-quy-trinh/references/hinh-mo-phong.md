# Hình mô phỏng 3D — phong cách, chiều sâu, prompt theo giây

## 1. Phong cách (giống video mẫu cầu Lư Câu)
- **Hoạt hình mô phỏng kỹ thuật 3D**: mô hình CGI sạch, đơn giản, chất liệu đều màu (đá, gỗ, đất, nước trong xanh), ánh sáng ban ngày đều, trời trong. Nhìn biết ngay là đồ hoạ máy tính minh hoạ kỹ thuật.
- **Vật thể tự chuyển động vào vị trí**: cọc cắm xuống, đá bay xuống khớp, khung gỗ dựng lên, lớp áo ốp vào — không cần người làm.
- **Một công trường, công trình tích luỹ**: cảnh sau bắt đầu đúng khung cuối cảnh trước (Studio Kịch Bản nối khung cuối).
- **Ba góc máy chính**: (1) mặt cắt nhìn ngang như bản vẽ, máy gần đứng yên — để giải thích lực; (2) nhìn chéo từ trên xuống — để xem lắp ghép; (3) đi dọc / lùi xa toàn cảnh — để thưởng ngoạn, cao trào.
- **Màu mũi tên**: đỏ = sức nặng / lực đè; vàng = lực đỡ / ma sát; xanh dương = nước, dòng chảy.
- Không người cận mặt, không chữ trong hình (chữ làm khi dựng).

## 2. Bộ hiệu ứng chiều sâu (mỗi cảnh ≥2, mỗi clip 10s tối đa 2)
| Hiệu ứng | Dùng khi | Cụm từ cho prompt |
|---|---|---|
| Mặt phẳng cắt quét | lộ cấu tạo bên trong | `a glowing section plane sweeps through the structure, revealing its interior layers` |
| Nhìn xuyên (X-quang) | thấy kết cấu giấu trong | `the outer layers turn semi-transparent X-ray view, showing the inner structure` |
| Bóc lớp | lớp áo → lõi → phòng | `layers peel away one by one from outside to inside` |
| Bung rời | bộ phận lắp ghép | `exploded view: the parts separate along their axes, then reassemble` |
| Máy chui vào trong | hành lang, phòng, đường hầm | `the camera flies through the wall into the corridor` |
| Zoom vĩ mô → vi mô | giải thích vật liệu (cát, vữa, thớ gỗ) | `continuous zoom from the wide view down to a grain-level macro view` |
| Bóng ma khung dây | cho thấy cái sẽ hỏng / sẽ thành | `a ghosted translucent wireframe preview shows …` |
| Đường lực động | sức nặng, ma sát, nước | `animated red arrows show the load pushing down, yellow arrows show the support pushing up` |
| Tua ngược / tua nhanh | về đá đầu tiên; xây cả trăm lớp | `reverse time-lapse, the layers retract from top to bottom` |
| Mặt cắt đất / nước | móng, cọc, kênh, lòng sông | `side cutaway through the ground showing sand, soil and bedrock layers` |

## 3. Viết `beats` khớp lời kể từng giây
- Ước thời lượng lời: ~3,5 âm tiết/giây. Chia lời cảnh thành 2–4 cụm; mỗi cụm = 1 nhịp hình có mốc giây.
- Khoảnh khắc chính rơi đúng lúc đọc từ khoá (vd "xé toạc" → tháp tách đôi ngay giây đó).
- Khuyết điểm: diễn sự cố (nghiêng, nứt, lún, xói) bằng hình trước, lời giải ở nhịp sau hoặc cảnh sau.
- Mẫu (cảnh 6 Kim tự tháp, lời: "Mỗi khối nặng vài tấn. Kéo trên cát thì cát cứ dồn đống trước mũi xe, kéo mãi không nhích. Nhưng bạn không chịu bỏ cuộc."):
```json
"beats": [
  ["0-3s", "a limestone block is lashed onto a wooden sledge, a big red arrow shows its weight pressing down; side cutaway shows the loose sand layer under the sledge"],
  ["3-7s", "the sledge is dragged forward, loose sand piles up in front of its nose, the sledge sinks, a red friction arrow grows larger"],
  ["7-10s", "the sledge stops, slow push-in on the sand pile"]
]
```

## 4. Câu cố định trong storyboard (chép nguyên, sửa tên công trình)
```json
"style": "3D technical simulation animation, clean simplified CGI models, smooth uniform materials, bright even daylight, educational engineering visualization like a construction documentary diagram, objects animate into place step by step by themselves, cutaway cross-sections and colored force arrows, clear 3D depth with foreground and background layers",
"lock": "no narration, no voices, soft ambient sound only; no text, letters or logos anywhere; no people in close-up; same construction site and same structure continuing from the previous video, construction progress accumulating",
"negative": "photorealistic, cinematic film look, live-action footage, drone footage, lens flare, text, letters, captions, watermark, logos, modern buildings, cars, cartoon characters, close-up faces, deformed structures"
```
Không bao giờ thêm chữ "photorealistic", "cinematic", "drone" vào `style` hay `beats`.

## 5. Cảnh ảnh thật (cảnh cuối)
Ghi `"real_photo": "File:<tên file Commons>"` + `"source"`; không tạo trong tool. `photo_clip.py` tải ảnh và làm clip zoom chậm đúng thời lượng lời kể của cảnh đó.

## 6. Tool & clip
- Studio Kịch Bản, mỗi cảnh 10s, 9:16, Veo3 · Omni Flash (mặc định macro). Lời kể một cảnh 8–12s (clip được làm chậm/nhanh tối đa ±20% cho khớp).
- Clip Studio Kịch Bản 720×1280 có logo Gemini (ngôi sao góc phải dưới) → `photo_clip.py --delogo` (vùng 574,1134,54×54).

## 7. TRẠNG THÁI XÂY DỰNG — chặn lỗi "chưa xây mà đã thấy công trình xong" (anh chỉ ra 11/11/2026)
Tool (Veo) có "ký ức" rất mạnh về công trình nổi tiếng: thấy tên công trình hay chữ "wall/pyramid/bridge" là vẽ luôn bản hoàn chỉnh. Phải ép nó chỉ vẽ cái ĐÃ xây tới cảnh đó:
1. **Không đưa tên công trình vào `style` / `settings` / `lock`.** Bối cảnh chỉ tả địa hình, trời, ánh sáng ("a rugged green mountain ridge, clear sky"). Tên chỉ xuất hiện ở cảnh `hoan_thanh`.
2. **Mỗi cảnh ghi 2 danh sách tiếng Anh** (bắt buộc, `prep.py` kiểm):
   - `da_co`: những gì ĐÃ có tại thời điểm cảnh này (vd `["flat bedrock platform", "one block on a sledge"]`; chưa có gì thì `[]` = nền trống).
   - `chua_co`: những gì CHƯA xây, CẤM xuất hiện (vd `["stone courses", "white casing", "ramp"]`).
   `prep.py` ghi vào prompt: `ALREADY BUILT at this exact moment: … NOT BUILT YET, must NOT appear anywhere in the shot: …` và thêm câu cấm vào `negative`.
3. **`ten_cong_trinh`** ở gốc storyboard: `["great wall"]` / `["pyramid"]` (chữ thường, tiếng Anh). Cảnh không có `"hoan_thanh": true` mà beats nhắc tên → `prep.py` báo lỗi. Khung dây / bản vẽ được phép nhưng phải ghi `ghosted wireframe …` hoặc `blueprint …` (xem cảnh 3 mẫu Kim tự tháp).
4. **Một phần chỉ được thêm vào `da_co`, không bao giờ lùi** (trừ cảnh `"tua_lai": true` = tua ngược / xé toạc). Phần đang được xây NGAY TRONG cảnh thì không ghi vào `chua_co` của cảnh đó (nó hiện ra trong cảnh).
5. **Khung đầu cảnh 1 (Kiểu A, mở bằng mặt đất trống):** tạo ảnh "mặt đất trống" bằng Ảnh AI rồi gắn vào cảnh 1:
   ```json
   "image_jobs": [{"prompt": "3D technical simulation render, a bare rugged ridge with only a few wooden survey stakes, NO wall, NO tower, NO building, clear sky, 9:16", "dest": "ref/khung_dau.jpg"}]
   ```
   `python $A/image_macro.py projects/<slug>/storyboard.json --auto --collect`, rồi cảnh 1 ghi `"first_last": ["ref/khung_dau.jpg"]`. Không có ảnh khung đầu thì tool tự mở bằng hình công trình xong.
6. **Kiểm sau khi tạo:** xem `_review.jpg` đối chiếu `da_co / chua_co` từng cảnh. Cảnh nào lộ phần "chưa có" → tạo lại cảnh đó (nhớ cảnh sau nối khung cuối → có thể phải tạo lại từ cảnh đó trở đi).
