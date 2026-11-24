# Mode 1 — KOC_REVIEW (video review có người nói)

Mục tiêu: người xem **hiểu nhanh hơn và tin hơn** nhờ graphic xuất hiện đúng lúc KOC nói từ khóa. Người nói luôn là trung tâm.

## Quy trình

1. `transcribe_elevenlabs.py video.mp4 -o words.json --script script.txt` (nếu có kịch bản thì chữ phụ đề sẽ đúng kịch bản, timing theo giọng thật).
2. Đọc `words.json`, chia beat theo ý: mở đầu/hook → vấn đề → sản phẩm → công dụng/số liệu → so sánh → giá/ưu đãi → kêu gọi.
3. Gắn graphic theo bảng "từ khóa → graphic" bên dưới. Mỗi graphic bắt đầu tại `start` của từ khóa (trừ 0.1s) và giữ đến hết cụm ý (thường 2–4s).
4. Chọn preset phụ đề (xem `subtitle-styles.md`). Review năng động: `pop_word` hoặc `keyword`. Review chuyên gia/số liệu: `box` hoặc `clean`.
5. Viết timeline → validate → `render.py --preview` → QA khung hình → render cuối.

## Từ khóa trong lời nói → loại graphic

| Khi KOC nói… | Graphic | Template |
|---|---|---|
| Con số có đơn vị: "giảm 87% dầu", "pin 20 tiếng", "giá 299k" | Số chạy từ 0 đến giá trị | `counter` |
| So sánh nhiều mức: "sau 1 tuần… 2 tuần… 4 tuần", "A 12h, B 8h" | Biểu đồ cột mọc lên | `bar_chart` |
| Liệt kê công dụng: "thứ nhất… thứ hai…", "vừa…, vừa…, lại…" | Danh sách tick hiện lần lượt, mỗi dòng đúng lúc được nói | `checklist` |
| Chỉ vào chi tiết sản phẩm: "cái vòi bơm này", "thành phần niacinamide" | Thẻ chú thích có đường chỉ tới vị trí | `callout` |
| "Trước và sau", "so với loại cũ", "hàng thật / hàng giả" | Hai cột đối chiếu | `compare` |
| Câu chốt, cảm thán: "đáng tiền!", "phải mua ngay" | Chữ lớn bật lên | `kinetic_text` |
| Nói về cảnh dùng sản phẩm mà khung hình không có | B-roll full khung 1.5–3s (giữ audio gốc) | layer `broll` |

Không có số liệu có nguồn thì **không** dùng `counter` / `bar_chart`. Thay bằng `checklist` hoặc `kinetic_text` nhắc lại đúng lời nói.

## Dữ liệu (`data`) của từng template

```jsonc
// counter
{ "value": 87, "from": 0, "decimals": 0, "prefix": "", "unit": "%", "label": "giảm dầu thừa",
  "source": "Thử nghiệm của hãng, 2025" }            // hoặc "illustrative": true
// bar_chart
{ "title": "Độ ẩm da sau khi dùng", "unit": "%", "source": "…",
  "items": [ {"label":"Tuần 1","value":32}, {"label":"Tuần 2","value":54}, {"label":"Tuần 4","value":78,"highlight":true} ] }
// checklist — "times": thời điểm (giây, tuyệt đối) từng dòng hiện ra, lấy từ start của từ khóa
{ "title": "Công dụng", "items": ["Kiềm dầu 8 tiếng", "Mờ thâm", "Không bết dính"], "times": [12.4, 13.6, 15.0], "icon": "check" }
// callout — target: điểm cần chỉ (tỉ lệ khung 0–1); card tự đặt sang phía còn lại
{ "text": "Niacinamide 10%", "sub": "giúp mờ thâm", "target": [0.62, 0.55] }
// compare
{ "left":  {"title":"Trước", "lines":["Da dầu", "Lỗ chân lông to"]},
  "right": {"title":"Sau 4 tuần", "lines":["Khô thoáng", "Mịn hơn"]}, "vs_text": "VS" }
// kinetic_text — style: word_pop (mặc định: từng từ bật lên có nảy, dòng nhấn phát sáng màu nhấn + gạch chân chạy ra từ giữa)
//                       | pop | slide | typewriter ; "glow": false để tắt phát sáng (vd caption trên)
{ "lines": ["ĐÁNG TIỀN", "TỪNG ĐỒNG!"], "emphasis_index": 0 }
```

## Bố cục 9:16 (1080×1920)

- **Vùng mặt**: y 15–45%, không đặt graphic ở đây. Nếu khuôn mặt nằm lệch, dùng anchor `middle_left`/`middle_right` ở phía trống.
- `top` (y≈8–14%): counter, kinetic_text ngắn.
- `lower_third` (y≈55–68%): checklist, compare, bar_chart. Nằm trên phụ đề, không đè lên nhau.
- Phụ đề: y≈72–82%. Đáy 12% và mép phải 12% để trống cho nút của nền tảng.
- Mỗi lúc tối đa 1 graphic chính + phụ đề. Hai graphic không chồng nhau về thời gian.

## Nhịp

- Graphic vào 8–12 frame (ease-out), giữ đủ để đọc (≥ 1.2s cho mỗi 10 ký tự), ra 6–10 frame.
- 1 graphic cho mỗi 4–8 giây là đủ. Phần còn lại để người nói + phụ đề.
- Không zoom giật, không flash, không rung, trừ khi người dùng yêu cầu.
