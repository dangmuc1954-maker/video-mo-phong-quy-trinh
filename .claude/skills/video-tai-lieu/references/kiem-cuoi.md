# Kiểm cuối độc lập (luật P2) — làm TRƯỚC khi gửi anh duyệt

Người dựng luôn "thiên vị" sản phẩm của mình. Trước khi gửi anh, giao cho **một agent mới (Agent tool, context sạch)**
soát video. KHÔNG kể cho nó quá trình làm, lý do, hay "chắc là ổn rồi" — chỉ đưa đầu vào bên dưới.

## Chuẩn bị đầu vào (1 lệnh)
`python $V/review_sheet.py projects/<slug> [--video 2-xuat/<file>.mp4]`
→ `render/review/`: mỗi cảnh 3 khung (vừa vào · giữa · sắp hết) ghép thành `sheet_XX.jpg` (8 cảnh / tờ, ghi giây + cảnh + lời thoại),
`brief.md` (tóm tắt storyboard: lời thoại, module, từ khoá, callout, nguồn từng cảnh) và `rule_report.md` đã có.

## Lời giao việc cho agent kiểm (dán nguyên, thay <slug>)
> Bạn là người kiểm video độc lập. Đọc `projects/<slug>/render/review/brief.md`, xem lần lượt mọi ảnh `sheet_*.jpg`
> trong cùng thư mục (Read), đọc `.claude/skills/video-tai-lieu/references/luat-dung.md` và mục "Tự kiểm" trong
> `.claude/skills/ai-semantic-video-editor/references/bo-nao-dao-dien.md`. Soát từng cảnh theo danh sách dưới.
> Với mỗi lỗi ghi: mã luật · cảnh · giây · mô tả ngắn · cách sửa. Không khen, không đoán; không chắc thì ghi "cần xem video".
> Ghi kết quả vào `projects/<slug>/render/review_report.md`, dòng cuối là `KẾT LUẬN: ĐẠT` hoặc `KẾT LUẬN: CẦN SỬA (n lỗi)`.

## Danh sách soát
- **Nội dung:** chữ trên hình khớp câu đang đọc (C1); số liệu có nguồn hiện trên hình (Q1); không có khẳng định thiếu bằng chứng.
- **Tên riêng:** mỗi tên phần mềm / tổ chức được đọc có logo hoặc ảnh thật đúng lúc (Q2).
- **Bố cục:** chữ không đè, không tràn, không bị logo/khung che; chữ cần đọc đủ to ở cỡ điện thoại (Q11) — thu nhỏ tờ ảnh còn đọc được không?
- **Nhịp:** tiêu đề lớn không treo (R5); mỗi 5–8s có thứ mới (R6); thông tin chốt có thời gian đứng (R1); không có cảnh nào lặp ý (P4).
- **Thẩm mỹ:** mỗi kiểu graphic "đinh" chỉ 1 lần (Q6); hiệu ứng sáng không rắc tràn lan (Q4); máy quay không rung vô cớ (Q3).
- **Chính tả & dấu tiếng Việt:** sai dấu, thiếu chữ, chữ lạ trong cảnh AI (nhòe, chữ ngoằn ngoèo).
- **Kỹ thuật:** khung đen, khung trắng, khung giật, video quay màn hình bị trống / sai đoạn.

## Sau khi có báo cáo
Sửa hết lỗi "CẦN SỬA" → dựng lại phần liên quan → chạy lại agent kiểm (agent MỚI) cho tới khi `ĐẠT`. Gửi anh video kèm 1 dòng "kiểm độc lập: ĐẠT".
