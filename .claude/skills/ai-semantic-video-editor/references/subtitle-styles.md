# Phụ đề tiếng Việt đa phong cách

`make_subs.py words.json -o build/subs --preset <tên> [--keywords "từ1,từ2"] [--uppercase]` tạo ra `subs.ass` (để render) và `subs.srt` (để import vào CapCut, rồi chọn style có sẵn của CapCut).

| Preset | Mô tả | Hợp với |
|---|---|---|
| `clean` | Chữ trắng, viền đen dày, cả cụm, mờ vào/ra | Mọi loại, an toàn nhất |
| `box` | Chữ trắng trên hộp nền tối bán trong suốt | Review chuyên gia, nền nhiễu |
| `karaoke` | Cả cụm hiện, chữ được nói đổi màu theo đúng timing từng từ | Review năng động, nhạc |
| `pop_word` | 1–3 từ mỗi lần, chữ to, từ đang nói bật lên + đổi màu nhấn | TikTok/Reels, hook |
| `keyword` | Như `clean` nhưng từ khóa (beats[].keywords hoặc `--keywords`) to hơn và đổi màu nhấn | Review công dụng, số liệu |
| `cinematic` | Chữ nhỏ thanh, màu kem, mờ chậm, đặt thấp | Kể chuyện, đạo lý |
| `story_pop` | **Mặc định cho video có giọng kể.** Cả cụm giữ chỗ sẵn, mỗi từ hiện ra đúng lúc được đọc (mờ vào + bật 60%→116%→100%), từ đang đọc có màu nhấn rồi chuyển trắng | Kể chuyện, đạo lý, review không KOC, giải thích |

Màu nhấn lấy từ `style_bible.palette[2]`, font lấy từ `style_bible.font` (khi gọi qua `render.py`).

## Quy tắc ngắt cụm

- Ngắt sau dấu `. , ! ? ; :` hoặc khi có khoảng lặng > 0.35s.
- Tối đa ~28 ký tự/dòng, 2 dòng (9:16); `pop_word` tối đa 3 từ.
- Không tách các cụm dính nghĩa: số + đơn vị ("87 %"), tên riêng, "không + động từ". Chỉnh lại trong `words.json` nếu cần.
- Phụ đề không được xuất hiện trước khi lời nói bắt đầu. Cho phép giữ thêm tối đa 0.3s sau khi nói xong để kịp đọc.

## Kiểm tra

- Đúng chính tả và đủ dấu (so với kịch bản).
- Không che miệng, mắt hay sản phẩm (mode 1).
- Đọc kịp: tối đa ~17 ký tự/giây.
