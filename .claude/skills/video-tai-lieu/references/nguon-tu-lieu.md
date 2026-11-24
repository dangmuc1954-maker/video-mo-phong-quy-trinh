# Nguồn dữ liệu, tư liệu và bản quyền

## Dữ liệu (số, mốc, tên)
- Thứ tự ưu tiên: tài liệu anh đưa → trang chính thức (chủ đầu tư, cơ quan nhà nước, doanh nghiệp) → báo lớn (VnExpress, Tuổi Trẻ, Thanh Niên, VTV, Reuters…) → Wikipedia (chỉ để định hướng, kiểm chéo).
- Mỗi số trong video có trong `facts.json` kèm link. Hai nguồn lệch nhau → dùng nguồn chính thức, ghi "theo …".
- Dự án đang bán / sản phẩm: ghi "theo chủ đầu tư" hoặc "theo nhà sản xuất"; không khẳng định thay họ.
- Không có nguồn → không dùng, hoặc ghi rõ "(ước tính)" khi là phép tính của mình từ số có nguồn.

## Ảnh
- Wikimedia Commons (fetch_assets tự lấy tác giả + giấy phép CC). Ghi `Ảnh: <tác giả> / <giấy phép>` trên khung ảnh và trong mô tả video.
- Ảnh báo chí về sự kiện / nhân vật thời sự: chỉ khi thật cần, ghi nguồn báo; ưu tiên ảnh anh tự có quyền dùng.
- Không dùng ảnh máu me, xác người, nạn nhân là trẻ em, ảnh riêng tư. Không ghép mặt, không chỉnh ảnh người thật để gây hiểu sai.

## Tìm ảnh/video bằng chứng (làm như thế này)
1. Commons theo chủ đề: API `categorymembers` của category chủ đề (vd "Category:Ho Chi Minh City Metro Line 1") + `search`, tải thumbnail ghép bảng → Claude XEM bằng mắt, chọn đúng cảnh (đông/vắng, đúng nơi). Bị 429 thì giãn nhịp (≥1s/yêu cầu).
2. Openverse API (`api.openverse.org/v1/images/?q=…&license_type=commercial,modification`) — gom Flickr/Commons giấy phép mở.
3. Báo chí / trang chính thức: lấy URL ảnh trong bài (thẻ img, chú thích "Ảnh: …"), ghi `source` = tên báo/tác giả.
4. Mạng xã hội (FB, Threads, Instagram, TikTok, YouTube): bài công khai → link vào `bg_video` / `photo`; yt-dlp tải video. Bài riêng tư / cần đăng nhập → nhờ anh tải hoặc cho dùng cookie trình duyệt. Ghi nguồn, đưa vào danh sách credits cho anh duyệt.
Ảnh của bên thứ ba (báo, mạng xã hội) có bản quyền của người chụp: video kiếm tiền thì nên xin phép hoặc dùng làm dẫn chứng ngắn có ghi nguồn; anh quyết định trước khi đăng.

## Bản đồ
- Toạ độ: OpenStreetMap Nominatim (ghi "© OpenStreetMap"), tối đa 1 yêu cầu/giây.
- Ảnh vệ tinh: Esri World Imagery — ghi "Ảnh vệ tinh: Esri, Maxar, Earthstar Geographics". Esri cho phép hiển thị kèm ghi công; với kênh kiếm tiền lớn, nên dùng tài khoản ArcGIS hoặc nguồn có giấy phép thương mại (Mapbox, Google Earth Studio có điều khoản riêng) — báo anh khi kênh bắt đầu kiếm tiền.

## Icon, font, chất liệu
- Icon Lucide (ISC), font Be Vietnam Pro / Oswald / Playfair Display (OFL) — dùng thương mại được.
- Chất liệu giấy, gỗ, hạt phim, ánh sáng: dựng bằng code trong engine (không cần tải).

## Nhạc & SFX
- Nhạc nền / SFX lấy trong thư viện CapCut (đã có bản quyền dùng trong CapCut) hoặc nhạc anh có quyền dùng. Không lấy nhạc từ video người khác.
