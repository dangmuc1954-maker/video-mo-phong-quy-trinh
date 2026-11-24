# Bộ luật dựng (đánh số) — tự kiểm mỗi video

Gom các yêu cầu anh đã duyệt + bài học từ video-shotcraft (Apache-2.0, tham khảo, không chép mã).
Mỗi luật = **luật** + **vì sao** + **tự kiểm**. Mã số không đánh lại; luật mới chỉ thêm vào cuối nhóm.
Được cố ý vi phạm khi phong cách cần, nhưng phải ghi lý do vào `storyboard.json → "rule_notes"`.

`python $V/rule_check.py projects/<slug>` tự soát các luật có dấu ⚙ → `render/rule_report.md` (✓ / ✗ kèm cảnh, giây).
Luật không tự soát được thì kiểm bằng mắt trên khung hình và ở bước kiểm cuối độc lập (`kiem-cuoi.md`).

## R — Nhịp
- **R1 ⚙ Chốt xong phải thở.** Thông tin quan trọng (số lớn, chữ chốt, logo) hiện xong phải đứng yên ≥1s trước khi cắt cảnh. Tự kiểm: mốc `cue` nào rơi vào 0.8s cuối cảnh là quá sát.
- **R2 Nhóm bay vào nhanh dần, xong dừng 0.5s.** Liệt kê nhiều thứ: khoảng cách giữa các món ngắn dần (`stagger: "accel"`), món cuối vào xong thì đứng 0.5s. Chuyển động đều tuột = kiểu PowerPoint rẻ tiền.
- **R3 Thà chậm hơn nhanh.** Bản đầu thường nhanh quá: động tác chính của cảnh mở ≥3s, thao tác màn hình chạy bằng tốc độ người thật.
- **R4 ⚙ Cú rung cả khung ≤3 lần / video.** Chuyển cảnh `flash`, `flash_red`, `slam` và chữ chốt nặng (`stamp_slam`, `warning`, `crack`) tính là "cú đập": tổng ≤ 1 lần / 8s và cú rung cả khung (flash/slam) ≤3 trong cả video, dồn vào hook và cao trào.
- **R5 ⚙ Tiêu đề lớn không treo đơ** (anh yêu cầu 11/11/2026): cảnh `title` > 2.6s phải có `p.then`; tiêu đề chỉ đập ~1.2s rồi bay ra / thu thành nhãn.
- **R6 ⚙ Không có đoạn "câm hình" > 3s:** mỗi 5–8s phải có móc mới (từ khoá, nhịp graphic, callout, chuyển cảnh).

## Q — Hình
- **Q1 Bằng chứng thật.** Khẳng định chuyện ngoài đời → ảnh/video thật có nguồn (bộ não 5b). Không bịa số, ảnh, trích dẫn.
- **Q2 ⚙ Gọi tên là có logo / ảnh thật** (quy tắc 4b): phần mềm → logo chính thức; tổ chức/người/nơi → ảnh thật; liệt kê sự vật → ảnh từng thứ.
- **Q3 Máy quay không rung vô cớ.** Rung chỉ dùng cho tông căng thẳng/sốc; cảnh thông tin sáng thì đứng vững.
- **Q4 Hiệu ứng sáng (loé, quét sáng) chỉ cho nhân vật chính, 1 lần / cảnh,** không rắc cho cả đàn; phải nằm trong góc bo của thẻ.
- **Q5 Mở đầu một nhân vật chính** với một đường động tác trọn vẹn, không nhồi nhiều thứ cùng nhảy.
- **Q6 ⚙ Mỗi kiểu graphic "đinh" chỉ làm vai chính 1 lần** (converge, transform, waffle, duo, prompt_video, people, breakout, dot_number, timeline, slider, orbit3d, exploded3d…). Lặp = nhàm.
- **Q7 Phần tử bay vào phải có chỗ đáp thật** (khe trong bố cục), không lơ lửng vô định.
- **Q8 ⚙ Không để nền đen trơn kéo dài** (anh nhắc 11/11/2026): graphic phải đặt trên nền tư liệu thật — `bg_video` / `bg_photo` (cảnh AI có ghi "minh hoạ", ảnh thật có nguồn), quay màn hình, ảnh trong thẻ. Không quá 2 cảnh liền nhau chỉ có nền trơn; module mới (orbit3d, exploded3d, dot_number, breakout…) cũng vậy.
- **Q9 ⚙ Graphic KHÔNG che bằng chứng** (anh yêu cầu 11/11/2026). Ảnh/video/quay màn hình làm dẫn chứng phải lộ trọn; graphic chỉ được nằm CẠNH hoặc VIỀN nó:
  - Quay màn hình có chữ chốt → `p.side: "left"` (cửa sổ dồn trái ~60%) và chữ chốt đặt vào **cột phải**: `{"x": 82, "w": 30, "pos": 35}` (hoặc ngược lại `side: "right"` + `x: 18`). Không chữ chốt → cửa sổ căn giữa như cũ.
  - Thẻ ảnh / timeline / khung video / trước–sau → chữ chốt ở dải trống (trên hàng thẻ, dưới kicker), không đè thẻ, nhãn, khung.
  - Được phép đặt TRÊN bằng chứng: khoanh viền (`rings`), đóng băng (`freeze`), con trỏ — vì chỉ làm nổi, không che.
  - Logo/callout ở góc NGOÀI vùng bằng chứng. Nền video làm mờ là trang trí → graphic được nằm trên; nền là bằng chứng thì không làm mờ, không đè.
  - **Quay màn hình / video thao tác KHÔNG BAO GIỜ làm nền mờ** (anh nhắc 11/11/2026: "graphic đè video hoạt động phía sau, không ai biết gì"). Muốn cho xem tool đang làm gì → module `screen` (hiện rõ, `side` + cột chữ/ảnh cạnh bên). `bg_video` + `bg_blur` chỉ dành cho cảnh trang trí (cảnh AI không mang thông tin). Đoạn lặng sau lời kể → chiếu kết quả rõ nét, không để graphic treo.
  - Sub cũng không được đè khung bằng chứng: cửa sổ quay màn hình / thẻ ảnh tự chừa dải sub dưới đáy.
  - Tự kiểm: `qa_layout.py` đo chữ chốt và sub × vùng `.qa-ev` (cửa sổ, khung video, thẻ ảnh, trước–sau) → lỗi "chữ chốt che bằng chứng"; `rule_check.py` báo cảnh bằng chứng có chữ chốt chưa xếp cột.
- **Q11 ⚙ Chữ đọc được trên điện thoại:** sub ≥4% cạnh ngắn (v2 ngang mặc định 4.4%), chữ cần đọc ≥2% (cảnh báo dưới 2.8%). Chữ chỉ để trang trí thì làm mờ hẳn; chữ đã muốn người xem đọc thì phải to — không có kiểu "muốn đọc mà đọc không nổi". `qa_layout.py` đo pixel thật.

## S — Âm thanh
- **S1 Tiếng thật, không tiếng game:** whoosh (lia), impact (đáp), riser (dồn), sparkle (loé), tiếng thật cho hành động (gõ phím, click, chụp ảnh). Không bíp bíp kiểu game trừ khi cố ý.
- **S2 ⚙ Chống "súng máy":** cùng một tiếng lặp dày (≥3 lần, cách nhau <0.7s) → xen 2 mẫu tiếng + âm lượng bậc thang giảm dần (0.40 → 0.25) + khoảng cách theo nhịp hình. `plan_timeline` tự làm.
- **S3 Âm thanh làm sau khi hình đã chốt;** hình đổi thời lượng thì soát lại toàn bộ mốc SFX (`capcut_sfx_check.py` phải in OK).
- **S4 Tiếng đúng hành động, dài đúng bằng hành động** (sfx_frames.py), không kêu lố sang cảnh sau.
- **S5 Câu âm thanh cao trào:** riser (dồn ~1.2s trước) → impact (đúng khung đập) → sparkle (ngay sau). Cảnh ghi `"climax": true` → `plan_timeline` tự thêm.
- **S6 Đỉnh âm ≤ -1 dB, không kéo to cả bài** (limiter không tự tăng mức).

## C — Lời / chữ
- **C1 Chữ trên hình khớp đúng câu đang đọc;** viết lại chữ sau khi hình đã chốt.
- **C2 Câu chốt cụ thể:** có tên thật / con số / lợi ích cụ thể, tránh khẩu hiệu chung chung.
- **C3 Tiêu đề ≤ 6 từ** (thu thành nhãn thì ≤ 3 từ).

## P — Quy trình
- **P1 Tự xem khung hình trước khi gửi anh** (`--stills`, `qa_layout`), không để anh là người phát hiện lỗi đầu tiên.
- **P2 ⚙ Kiểm cuối độc lập:** trước khi gửi, một agent mới (không biết quá trình làm) soát video theo `kiem-cuoi.md`, ghi lỗi kèm giây/cảnh.
- **P3 Phản hồi mơ hồ ("cái tiêu đề đầu") → hỏi lại đúng đối tượng trước khi sửa.**
- **P4 Mỗi cảnh phải mang thông tin mới;** cảnh/câu chốt lặp lại → bỏ.
