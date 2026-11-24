# Muse (muse.ai) — điều khiển qua Claude in Chrome

Đã chạy thực tế ngày 06/11/2026 với truyện Thỏ và Rùa: tạo 8 cảnh, tải đủ 8 cảnh.
Toạ độ bên dưới tính theo khung screenshot 1568 px ngang. Nếu khung khác, đổi lại bằng JS (xem mục "Tìm video").

## 0. Mở & kiểm tra đăng nhập
1. `tabs_context_mcp {createIfEmpty:true}` → `navigate https://muse.ai`.
2. Trang hiện "Đăng nhập hoặc tạo tài khoản" → **dừng, nhờ anh bấm chọn tài khoản**. Không tự đăng nhập.
3. Đã vào: thấy textbox "Nhắn tin" ở dưới, cột trái có "Đoạn chat chính" và "Đoạn chat phụ" kèm dấu **+**.
4. Muse trả lời "video generation isn't available for your account in your country or region" → tài khoản này không tạo video được, báo anh đổi tài khoản.

## 1. Gửi hàng loạt (mỗi chuỗi cảnh một chat phụ)
⚠️ Kích thước cửa sổ Chrome có thể đổi giữa chừng → **không bấm theo toạ độ cố định**. Mỗi cảnh:
```
find "Đoạn chat phụ mới button"        → ref nút "+"  (một lần cho cả đợt nếu không đổi trang)
left_click ref(+) → wait 2
find "message textbox Nhắn tin"        → ref ô nhắn tin (ref đổi sau mỗi lần mở chat mới → find lại)
[cảnh có ảnh: find "file input for attachments" → file_upload]
left_click ref(ô nhắn tin) → type "[<Tên video> - Cảnh N] <prompt>" → key Enter → wait 3
javascript_exec location.href           → phải ra /thread/<id>; nếu vẫn /thread/new = chưa gửi được → làm lại
```
Gửi liên tục 5–6 cảnh không cần chờ. Muse chạy song song; 5 cảnh cùng lúc xong trong khoảng 3–4 phút.

Cảnh nối tiếp (`continue_from_previous`): gửi **trong chat của cảnh trước**, sau khi cảnh trước đã có video, với tiền tố:
`[<Tên video> - Cảnh N] Lấy khung hình cuối của video vừa tạo làm khung hình đầu, rồi: <prompt>`

## 1b. Đính kèm ảnh tham chiếu (người thật / sản phẩm / chế độ khung hình), đã thử 06/11/2026
Cảnh có `reference_images` hoặc `first_last`: sau khi mở chat phụ mới và TRƯỚC khi gõ prompt:
1. `find "file input for attachments (input type=file)"` → lấy ref (nút "Đính kèm file" ẩn bên dưới).
2. `file_upload {ref, tabId, paths: ["<đường dẫn tuyệt đối>\projects\<slug>\ref\anh.jpg", …]}`. Có thể đưa nhiều ảnh, tổng < 10 MB.
   KHÔNG click vào nút đính kèm, vì nó mở hộp chọn file của Windows mà Claude không điều khiển được.
3. Ảnh hiện thành ô nhỏ trong khung nhắn tin (có dấu × để gỡ) → gõ prompt → Enter.
4. `first_last`: đưa đúng thứ tự [ảnh đầu, ảnh cuối] và mở đầu tin nhắn bằng **"tạo video chế độ khung hình"** (rule anh đã dặn Muse).
Ảnh tham chiếu để trong `projects/<slug>/ref/`. Ảnh quá 10 MB thì thu nhỏ trước: `ffmpeg -i in.jpg -vf scale=1440:-2 out.jpg`.

## Ghi chú tốc độ (06/11/2026)
- Ref thường giữ nguyên trong cả phiên: nút + = `ref_24`, ô đính kèm = `ref_393`, ô Nhắn tin = `ref_395` ở trang /thread/new, menu "Tải xuống" ≈ `ref_386–388`. Vẫn `find` lại nếu click báo lỗi.
- Muse xử lý các chat gần như LẦN LƯỢT: 3 cảnh gửi cùng lúc thì xong lúc khoảng 3, 6 và 7 phút. Kiểm tra cảnh gửi đầu tiên trước, trong lúc chờ thì làm việc khác.

## 2. Kiểm tra cảnh đã xong chưa
`navigate <URL chat>` → `wait 6` → JS:
```js
const k=1568/innerWidth;
[...document.querySelectorAll('video')]
  .filter(v=>v.videoWidth && v.videoWidth!==v.videoHeight)   // bỏ avatar vuông 480x480 của Muse
  .map(v=>{const r=v.getBoundingClientRect();
           return [v.duration,v.videoWidth,v.videoHeight,Math.round((r.x+r.width/2)*k),Math.round((r.y+r.height/2)*k)]})
```
- Mảng rỗng → chưa xong, hoặc video chưa nạp: chờ thêm 5–10s rồi chạy lại.
- Có video: `[10, 1152, 648, x, y]`. Muse trả 16:9 ở 1152×648 hoặc 1248×702, cả hai đều được.
- Chat có 2 video (cảnh nối tiếp): video thứ nhất là cảnh trước, video cuối là cảnh sau.
- Muốn xem hình để kiểm tra: `v.scrollIntoView({block:'center'})` rồi chụp màn hình.

## 3. Tải về: CHỈ dùng menu 3 chấm
1. Cuộn video vào giữa: `v.scrollIntoView({block:'center'})`. Video thường nằm ở (673, 457).
2. `hover` lên video (673, y) → `left_click (772, y)` (nút 3 chấm "Lựa chọn khác" bên phải video) → `wait 1`.
3. `find "Tải xuống menu item"` → `left_click ref` → `wait 6`.
4. File về `~/Downloads` với tên kiểu `hare-tortoise-scene5-20261106-1947-16x9.mp4`.
5. `python $S/collect_clip.py projects/<slug>/clips N` → chuyển thành `scene_NN.mp4` và in thời lượng/kích thước.
   Tải xong cảnh nào thì chạy collect ngay cho cảnh đó (script lấy file mới nhất), không tải dồn rồi mới collect.

⚠️ **KHÔNG** tải bằng JS (`<a download>.click()`). Chrome sẽ coi là trang tự tải nhiều file và **chặn muse.ai**, sau đó cả nút Tải xuống cũng không chạy nữa.
Nếu bị chặn (bấm Tải xuống mà Downloads không có file mới): nhờ anh vào Chrome, biểu tượng bên trái `muse.ai` trên thanh địa chỉ → Cài đặt trang web → **Tự động tải xuống → Cho phép**, rồi tải lại. Khi được mở lại, các lượt tải bị chặn trước đó có thể về luôn thành bản trùng `(1)`. Lúc đó lấy đúng file của cảnh theo tên (`sceneN`).

## 4. Làm lại một cảnh
Nhắn trong chính chat đó, nói rõ lỗi (bảng trong prompt-rules.md). Video mới là video **cuối** trong chat.
