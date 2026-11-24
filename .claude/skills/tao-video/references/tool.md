# Tool của anh — AI VIDEO LIBRARY (điều khiển qua computer use)

TRẠNG THÁI: ĐÃ HỌC 06/11/2026 (v3.1.3, mã nguồn của anh ở `D:\dự án antigravity\AIForge_Veo3_Studio`) — đã chạy thật Cách A: 2 cảnh Veo3 Omni 1.1 Flash 10s → 2 clip 1080p, tool_jobs.py lấy đủ.
> Cách B (Studio Kịch Bản) mới xem giao diện, chưa chạy thật — lần đầu dùng thì chụp màn hình từng bước.

## ⛔ 0a. Bẫy chống crack — TUYỆT ĐỐI KHÔNG
Tool do anh làm, có sẵn `security_trap.cjs` để chống khách crack. Bẫy không phân biệt ai: kích hoạt là app ghi mã máy NÀY vào danh sách đen trên server bản quyền của anh và tự tắt (anh phải vào trang admin gỡ ban). Vì vậy khi điều khiển: Không bao giờ:
- bấm **F12**, **Ctrl+Shift+I / J / C**, **Ctrl+U** khi cửa sổ tool đang ở trước;
- mở tool kèm cờ `--inspect`, `--remote-debugging-port`, `--remote-debugging-pipe`; không kết nối DevTools / CDP;
- sửa bất kỳ file nào trong `C:\Users\admin\AppData\Local\Programs\AI VIDEO LIBRARY\` hoặc `%APPDATA%\AI_VIDEO_LIBRARY_DATA\`.
Chỉ được: bấm chuột / gõ phím bình thường, và ĐỌC file trạng thái (script `tool_jobs.py` làm việc này).
Không vào License Center mua gói / nhập key, không đăng nhập hay đăng xuất tài khoản trong Browser Hub thay anh.

## 0. Thông tin chung
- Tên: **AI VIDEO LIBRARY** (app Electron, tác giả "Tris"). Lối tắt `C:\Users\admin\Desktop\AI VIDEO LIBRARY.lnk`
  → `C:\Users\admin\AppData\Local\Programs\AI VIDEO LIBRARY\AI VIDEO LIBRARY.exe`. Mở bằng `open_application "AI VIDEO LIBRARY"`.
- Dữ liệu: `%APPDATA%\AI_VIDEO_LIBRARY_DATA\` — `queue-state.json` (hàng đợi + trạng thái), `asset-state.json` (thư viện, có `localPath` của từng video), `assets\<id>.mp4` (file video).
- Nền tảng tạo video (mỗi loại cần tài khoản đăng nhập sẵn trong **Browser Hub**; máy anh đang có 9 Veo3, 3 Muse, 2 Grok):
  | Nền tảng | Model | Thời lượng | Ghi chú |
  |---|---|---|---|
  | **Veo3** (Google Flow) | **Omni 1.1 Flash** (mặc định) | 4 / 6 / 8 / 10s, 360p–720p | rẻ, nhanh; bật Upscale → 1080p |
  | Veo3 | Veo 3.1 Lite / Lite [LowPriority] / Fast / Quality | 8s | Quality tốn 100 tín dụng/video |
  | **Muse AI** | muse-video | 10s | giống chế độ Web nhưng chạy trong tool |
  | Grok | — | — | chỉ văn bản hoặc vài ảnh |
- Chế độ video: **Thành phần (Components)** = chỉ chữ (T2V) hoặc chữ + tối đa 3 ảnh tham chiếu (người / sản phẩm); **Khung hình (Frames)** = khung đầu (+ khung cuối), tối đa 2 ảnh.
- Tỉ lệ: 16:9, 9:16 (Studio Kịch Bản có thêm 1:1).
- Cửa sổ lúc học: phóng to toàn màn hình (màn siêu rộng, khung screenshot 1568×656). Mở app mà không thấy cửa sổ → PowerShell `ShowWindow(MainWindowHandle, 3)` + `SetForegroundWindow` để phóng to & đưa lên trước. Toạ độ dưới đây chỉ đúng khi phóng to trên màn này — màn khác thì tìm theo nhãn.

## ⭐ BẢN ĐỒ CHỨC NĂNG — chỉ dùng 3 studio: Ảnh AI · Video AI · Studio Kịch Bản
Anh chỉ định chỗ nào thì theo anh. Không chỉ định thì chọn theo bảng (Xưởng Video AI, TTS, Workflows: KHÔNG dùng trừ khi anh bảo):

| Anh yêu cầu / loại video | Vào đâu | Vì sao |
|---|---|---|
| **Video đồng nhất, liền mạch, "nối frame cuối", "theo kịch bản nối tiếp"**, câu chuyện quay liên tục | **Studio Kịch Bản** (dự án MỚI) | Dây chuyền tự lấy frame cuối cảnh trước làm tham chiếu cho cảnh sau, chạy lần lượt, dừng chờ khi có cảnh lỗi, tự ghép phim |
| Nhiều cảnh **độc lập** (quảng cáo, mẹo, review, KOC, hoạt hình nhiều bối cảnh) | **Video AI** + `tool_macro.py` | Chạy song song nhiều tài khoản, mỗi cảnh ảnh riêng, Upscale 1080p + xoá WM |
| **Trộn** nối tiếp + đổi bối cảnh, hoặc cần nối thật khít (khoá frame đầu) + 1080p | **Video AI** + bật **👑 Chuỗi Kịch Bản** | Dòng có ảnh = PROMPT KEY (🎬 Sang cảnh mới / 🔗 Nối tiếp), dòng không ảnh = Prompt con lấy frame cuối; chế độ **Khung hình** khoá frame cuối làm KHUNG ĐẦU |
| Cần **ảnh nhân vật / sản phẩm / khung đầu** trước khi làm video (anh không có sẵn ảnh, hoặc muốn nhân vật cố định cho mọi cảnh) | **Ảnh AI** trước → ảnh vào thư viện → dùng làm ảnh tham chiếu ở Video AI / Studio Kịch Bản | Một ảnh nhân vật chuẩn giúp mọi cảnh đồng nhất |

Kết quả chạy thật Studio Kịch Bản (07/11/2026, 2 cảnh hạc, Veo 3 · Omni Flash · 10s): cả chuỗi ~4 phút, clip **1280×720**, `tool_jobs.py collect` lấy đủ. Chỗ nối: cùng nhân vật, tư thế, bối cảnh, ánh sáng — nhưng KHÔNG khít từng pixel (khung cảnh 2 hơi lệch/gần hơn) → khi dựng CapCut dùng hoà tan ngắn 0,3–0,5s ở mép nối hoặc cắt bỏ ~0,3s đầu cảnh 2. Cuối clip có **logo ngôi sao Gemini** nhỏ góc phải dưới (không có xoá WM) → cắt/che khi dựng, hoặc dùng Video AI + Chuỗi Kịch Bản (có xoá WM) nếu anh cần sạch logo.

Khác biệt quan trọng giữa 2 cách nối cảnh:
- **Studio Kịch Bản**: frame cuối được dùng làm ẢNH THAM CHIẾU (R2V, chế độ Thành phần) — giữ nhân vật/bối cảnh đồng nhất, chuyển tiếp tự nhiên nhưng không khít từng pixel. Luôn **720p, không có Upscale / xoá WM**, cả chuỗi dùng **1 tài khoản** (tài khoản chọn cho dự án hoặc tài khoản đầu tiên) → dễ dính hết lượt giữa chừng; mỗi cảnh chờ tối đa 15 phút. Cảnh 2+ có ảnh riêng thì gửi [frame cuối + ảnh riêng].
- **Video AI + Chuỗi Kịch Bản**: giống trên, nhưng chọn được chế độ **Khung hình** (frame cuối = khung đầu thật), có Upscale 1080p + xoá WM, tài khoản tự chia.

## 1. Menu trái
Nhãn thật (tiếng Việt): Bảng điều khiển · **Studio** → Ảnh AI · **Video AI** (~38,115) · Xưởng Video AI · **Studio Kịch Bản** (~48,147) · Giọng đọc (TTS) · Workflows · Kho Workflow · *System:* **Hàng đợi** · Tài nguyên · **Tài khoản** (= Browser Hub) · Cài đặt · Gói & License. Góc dưới: tài khoản đăng nhập app + hạn mức.

## 2. Cách A — trang Video AI (mặc định: các cảnh độc lập, gửi hàng loạt)
Bố cục thật (phóng to):
- Tiêu đề "Studio Video AI" + cảnh báo "Cần nhập prompt". Góc phải trên: **Xóa đã chọn** (đỏ, ~1373,23 — KHÔNG bấm), **Chế độ Muse: Chờ đến khi xong** (~1457,23), nút chính (~1535,23) đổi nhãn theo tình trạng: "Xử lý lỗi" / "Kiểm tra prompt" / **"Tạo video N"** (tạo cho các dòng ĐANG TÍCH).
- Thanh "Hàng đợi Video" (y≈57): **👑 CHUỖI KỊCH BẢN: TẮT/BẬT** (~615) · 📁 thư mục lưu (~675) · ⚡ Tự động tải (~728) · 🔗 Tự động ghép (~805) · Chờ xong hết mới ghép (~883) · Chuyển cảnh (~995) · **Tự xóa** (~1120) · Biên tập video (~1203) · **+ Thêm prompt** (~1265) · **Nhập prompt** (~1327) · ô tìm kiếm · "N prompt / N video".
- Bảng: ☑ (tích tất cả ~117,79) | # | PROMPT / KỊCH BẢN | NỀN TẢNG AI | CÀI ĐẶT (tỉ lệ, thời lượng) | SỐ LƯỢNG | TÀI KHOẢN | TRẠNG THÁI | THAO TÁC (nhân bản, xoá). Mỗi dòng ~25px, dòng 1 ở y≈100.
- Dưới: "Kết quả xem trước" (Tất cả / Đang tạo / Hoàn thành / Thất bại, Thử lại tất cả lỗi, Xóa tất cả lỗi).
- **Bảng có thể đang chứa prompt cũ của anh** (lúc học có 8 dòng Muse "tạo con mèo"… Pending, đang tích sẵn). Trước khi bấm Tạo video: BỎ TÍCH dòng cũ (bấm ☑ tất cả 2 lần để bỏ hết rồi tích lại dòng mới), không xoá dòng của anh.

Các bước:
1. `python $S/tool_jobs.py export projects/<slug>/storyboard.json --refs --clip` → clipboard có các prompt cách nhau 1 dòng trống; `tool_refs/canhN.jpg` là ảnh của Cảnh N.
2. Bấm **Nhập prompt** → hộp "Nhập danh sách Prompt (Video Studio)":
   - Mục 1: ô **🏷️ Tên chung** (~550,100) gõ tên video → các dòng thành "Cảnh N <tên chung>". Bấm **Dán Clipboard** (~624,100) (hoặc click ô lớn + Ctrl+V). App tách theo dòng trống (nếu có), không thì mỗi dòng 1 prompt; tự bỏ chữ "Cảnh N:" ở đầu. Cột phải "DANH SÁCH PHÂN CẢNH" hiện từng cảnh để kiểm tra.
   - Mục 2 "ẢNH THAM CHIẾU HÀNG LOẠT": chế độ **Theo tên cảnh** (mặc định) / 1→1 / 1 cho tất cả. Nguồn **Tải từ máy tính** (~553,208) hoặc **Thư viện Tool**. Click vùng "Kéo thả danh sách ảnh…" (~624,250) → hộp chọn file Windows → gõ đường dẫn thư mục `tool_refs` vào ô File name, Enter, rồi Ctrl+A chọn hết ảnh, Enter. "Theo tên cảnh" ghép `canhN` vào Cảnh N (cũng nhận `1.png`, `scene_01`, `[@Tên]` trong prompt, hoặc tên nhân vật trùng tên ảnh). Mỗi cảnh nhận 1 ảnh.
   - Bấm **Nhập N prompt** (~1050,583). (Hủy ~992,583, Đóng ~1067,60.)
3. Click dòng mới đầu tiên → mở **ngăn chi tiết bên phải** (che bảng; đóng bằng X ~1553,23):
   - Đầu ngăn: "Prompt #N", tên cảnh, nút trước/sau, nhân bản, xoá.
   - PROMPT / KỊCH BẢN (ô sửa prompt, Ctrl+Enter = thêm prompt mới — tránh bấm).
   - **NỀN TẢNG AI**: dropdown (~1525,178) Veo3 / Grok / Muse AI; dòng dưới là tài khoản (Tự động) + Cookie JSON (không đụng).
   - **ĐẦU RA**: model (~1478,254, vd muse-video / Omni 1.1 Flash / Veo 3.1…), tỉ lệ (~1425,272), số video (~1477,272), thời lượng (~1530,272); với Veo3 có thêm chế độ video, độ phân giải, Upscale tự động, Xóa watermark. Nút **Áp dụng cho mục chọn** (~1438,296) / **Áp dụng cho tất cả** (~1517,296 — áp cho CẢ dòng cũ của anh, nên dùng "mục chọn" khi bảng còn dòng cũ).
   - **ẢNH THAM CHIẾU**: nút **Thêm** (~1537,332) / "Thêm ảnh tham chiếu" — thêm ảnh thứ 2–3 bằng tay nếu cảnh cần.
4. Chỉ tích các dòng mới → bấm nút chính **Tạo video N** (~1535,23). Thông báo "N tác vụ video đã vào hàng đợi".
5. Theo dõi + lấy clip **không cần chụp màn hình**: `python $S/tool_jobs.py collect projects/<slug>/storyboard.json --wait 900` (chạy nền).
- Thanh trên của trang: **⚡ Tự động tải** (để TẮT — script lấy file trong thư viện), **🔗 Tự động ghép** (để TẮT — mình dựng bằng CapCut), **⏱️ Tự xóa** (PHẢI để "Tắt (Giữ vĩnh viễn)", nếu không file bị xoá trước khi script lấy).

### 2b. Kinh nghiệm từ lần chạy thật (06/11/2026, video thử 2 cảnh)
- App nằm sau cửa sổ khác: `open_application` KHÔNG kéo được lên → dùng PowerShell `ShowWindow(h,3)` + `SetForegroundWindow(h)` (h = MainWindowHandle của process "AI VIDEO LIBRARY" có tiêu đề).
- Sau **Nhập N prompt**: dòng mới thêm vào CUỐI bảng, được tích sẵn; dòng cũ tự bỏ tích; nút chính thành "Tạo video N". Tên dòng là "Cảnh <số thứ tự trong bảng>" (vd Cảnh 9, Cảnh 10), không theo Tên chung → script nhận cảnh theo nội dung prompt, không theo tên.
- Prompt nhập vào mặc định **Veo3 · Veo 3.1 - Fast · 8s · 720p** (20 tín dụng). Đổi trong ngăn chi tiết: model (~1478,288) → **Omni 1.1 Flash** (dòng đầu danh sách, ~1440,307); thời lượng (~1530,307) → **10s** (dòng cuối, ~1525,368) → 15 tín dụng; bật **Upscale tự động** (~1540,347) và **Xóa watermark Gemini** (~1540,379); bấm **Áp dụng cho mục chọn** (~1439,411) → thông báo "Đã áp dụng cài đặt từ Video Prompt #9 cho 2 prompt". Kiểm tra cột CÀI ĐẶT có "10s · Upscale 1080p · Bật xóa WM".
- Cuộn bảng: chỉ cuộn được khi trang đang ở đầu. Nếu lỡ cuộn cả trang: cuộn lên 30 nấc ở (700,400) rồi mới cuộn bảng ở (700,150).
- **Bấm Tạo video xong LUÔN kiểm tra bằng `tool_jobs.py status`** sau ~5 giây. Lần đầu bấm, app không gửi gì mà còn tự tích thêm 1 dòng cũ và mở ngăn chi tiết của nó → phải bỏ tích dòng cũ, xem lại nút ghi đúng "Tạo video N" rồi bấm lại. Lần thứ hai thì có thông báo "N tác vụ video đã vào hàng đợi".
- Lỗi gặp thật: `PUBLIC_ERROR_UNUSUAL_ACTIVITY` (Google nghi bất thường, job Failed ngay, KHÔNG tự thử lại) và `QUOTA_EXCEEDED` (app tự đổi tài khoản và chạy tiếp). Tạo lại 1 cảnh lỗi: chỉ tích dòng đó → "Tạo video 1". Lỗi UNUSUAL_ACTIVITY lặp lại nhiều lần → dừng, báo anh (đừng ép tài khoản Google), hoặc đổi dòng đó sang Muse AI.
- Thời gian thật: Omni 1.1 Flash 10s + upscale 1080p ≈ 1 phút/cảnh.

### 2c. Macro `tool_macro.py` (07/11/2026) — cách mặc định cho Cách A
- Không cần cài gì (ctypes + PIL có sẵn). Toạ độ cho màn 3440×1440 scale 100%, app phóng to.
- Nhận diện trạng thái màn hình bằng màu: hộp Nhập = nút "Đóng" đỏ hồng (1050-1088, 52-68); hộp chọn ảnh = nút "Dùng ảnh đã chọn" sáng (1120-1186, 518-536); ngăn chi tiết = ô "Prompt #N" có viền trắng (1400-1436, 17-29); còn lại = trang thường.
- **Gắn ảnh trong hộp Nhập không ăn** (v3.1.3: hộp hiện ảnh đã ghép nhưng dòng tạo ra vẫn "Chỉ văn bản") → macro chỉ dùng hộp Nhập để NẠP ảnh vào thư viện, rồi gắn từng cảnh bằng ngăn chi tiết → **Thêm** (1537,447) → hộp chọn ảnh: ô tìm (1110,150) Ctrl+A gõ tên → ảnh đầu (437,225) → **Dùng ảnh đã chọn** (1153,527). Tên ảnh lấy từ `asset-state.json` theo sha256 (app gộp ảnh trùng nội dung, giữ tên lần nạp đầu). Ảnh đặt tên `ref-<chữ>` không chứa số để "Theo tên cảnh" không ghép nhầm.
- Đi giữa các cảnh trong ngăn chi tiết: nút ‹ "Prompt trước" (1470,23).
- Tỉ lệ: dropdown (1425,307) → 16:9 (y≈325) / 9:16 (y≈341).
- Sự cố đã gặp khi làm macro (để không lặp lại): cửa sổ Claude nổi đè nút → macro bấm trượt, gõ nhầm vào prompt của anh (đã sửa: app TOPMOST + kiểm tra trạng thái); hộp Nhập giữ nội dung cũ → nhân đôi prompt (đã sửa: dọn trước khi dán); Claude bấm tay X khi ngăn đã đóng → trúng Tạo video, tạo nhầm 6 cảnh thử (90 tín dụng) — vì vậy luôn dùng `--only-generate` thay vì bấm tay.

### 2d. "Áp dụng cho mục chọn / tất cả" chép CẢ ảnh tham chiếu (đọc code 07/11/2026) — Video AI và Ảnh AI
Nút chép sang các dòng đang tích: nền tảng, chế độ, tỉ lệ, số lượng, thời lượng, model, độ phân giải, tài khoản, Upscale, xoá WM **và `referenceAssetIds` (ảnh tham chiếu / khung đầu)** của dòng đang mở.
- Mọi cảnh dùng CHUNG 1 ảnh (vd ảnh gia đình) → gắn ảnh ở 1 dòng rồi **Áp dụng cho mục chọn** là xong, KHÔNG gắn tay từng dòng.
- Mỗi cảnh ảnh RIÊNG (vd khung đầu từng cảnh) → **Áp dụng TRƯỚC**, rồi gắn ảnh riêng từng dòng; làm ngược lại thì ảnh dòng đang mở đè lên mọi cảnh.
`tool_macro.py` tự chọn đúng thứ tự này.

### 2e. Chế độ Khung hình (đồng nhất nhân vật mạnh nhất, đã chạy thật 07/11/2026)
> **Anh dặn 11/11/2026:** chỉ có **1 ảnh tham chiếu** (sản phẩm, nhân vật) → dùng chế độ **Thành phần** (mặc định, KHÔNG `--frames`). `--frames` (Khung hình) chỉ khi thật sự cần khung đầu/khung cuối; gắn kiểu thường hay lỗi "needs a start frame" và kẹt Pending.
`tool_macro.py … --frames`: bấm **Khung hình** (1517,239) trong ngăn chi tiết; mục ảnh đổi thành "KHUNG THAM CHIẾU · Cần khung đầu", nút **Thêm** vẫn ở (1537,447); ảnh gắn vào = **Khung đầu** (I2V). Storyboard ghi ảnh ở `first_last: ["ref/canh-N.jpg"]` (chỉ khung đầu).
Quy trình đồng nhất nhân vật cho video nhiều bối cảnh (vd vlog gia đình):
1. **Ảnh AI**: 1 ảnh nhân vật chuẩn (`image_jobs` trong storyboard) → `tool_jobs.py images <sb> --wait 300` chép về `ref/`.
2. **Ảnh AI**: N ảnh khung đầu, mỗi cảnh 1 ảnh, GẮN ảnh nhân vật chuẩn (gắn 1 dòng → Áp dụng cho mục chọn) + bật Xoá watermark → `images --only ref/canh-*.jpg`.
3. **Video AI** `--frames`: mỗi cảnh bắt đầu đúng từ khung đầu của nó.
Ảnh trong thư viện tool thường tên chung chung (Canh_5.png…) → sau khi macro gắn, mở ngăn từng dòng (‹ ›) zoom kiểm tra đúng ảnh trước khi tạo.

## 3. Studio Kịch Bản — video đồng nhất, nối frame cuối (ĐÃ HỌC + chạy thật 07/11/2026: chuỗi 2 cảnh Veo 3 · Omni Flash · 10s)
Menu: Studio → **Studio Kịch Bản** (~48,147). Tiêu đề "STUDIO KỊCH BẢN PHIM — nối tiếp cảnh đa dự án".
**Cách chạy (đọc từ code):** chạy LẦN LƯỢT. Cảnh 1 dùng ảnh riêng (nếu có); cảnh 2+ gửi [frame cuối cảnh trước + ảnh riêng] làm ảnh tham chiếu (R2V). Cả chuỗi dùng 1 tài khoản (ô tài khoản của dự án, "Tự động chia" = tài khoản đầu tiên). Mỗi cảnh chờ tối đa 15 phút; cảnh lỗi → dây chuyền DỪNG chờ, bấm 🔄 Tạo lại ở cảnh đó để chạy tiếp từ đó. Luôn 720p, KHÔNG có Upscale / xoá WM. Xong hết + "Tự Động Ghép Phim: BẬT" → tự ghép phim (chuyển cảnh theo ô Chuyển cảnh).

Bố cục (app phóng to):
- Hàng tab dự án (y≈45): animal · Dự Án Kịch Bản 2 · 3 … — **của anh, KHÔNG sửa/xoá**. Rê chuột lên tab đang chọn hiện ✏️ đổi tên (~548) và ✕ xoá (~557) ở cuối tab; xoá hỏi bằng hộp xác nhận Windows ("Bạn có chắc chắn muốn xóa "<tên>" không?" → OK ~803,316).
- **+ Thêm Dự Án Mới** (1527,23) → tạo "Dự Án Kịch Bản N" có sẵn 2 cảnh mẫu (con mèo), Muse AI · 16:9 · 10s, tự chuyển sang tab mới.
- Thanh công cụ (y≈82): **Nhập Danh Sách Prompt** (158) · + Thêm Cảnh (230) · Dọn Cảnh (281) · Tự Động Ghép Phim: BẬT (352) · Tự Động Tải: BẬT (438) · Chờ xong hết mới ghép (515) · Chuyển cảnh (640) · Thư mục lưu (712) · tài khoản "Tự động chia" (785). Phải: Biên Tập Video · **🎬 TẠO VIDEO KỊCH BẢN (N cảnh)** (~1497,82).
- Mỗi cảnh là 1 thẻ: "Cảnh 1 · Mở đầu" + **Ảnh đầu vào (+)** (126,175); Cảnh 2+ "🔗 Nối tiếp" + **Ảnh tham chiếu (+)** (126,321 với cảnh 2 khi mỗi thẻ cao ~146px). Ô prompt. Hàng ô chọn của cảnh 1 (y≈230): **nền tảng** (137) · **model** (185, chỉ hiện với Veo 3) · **tỉ lệ** (226) · **thời lượng** (256). Dưới: ▶ chạy riêng cảnh, 🗑 xoá cảnh.
- Các ô chọn là ô chọn GỐC của Windows (danh sách nền trắng khó đọc) → **dùng phím**: bấm ô → phím → Enter.
  - Nền tảng: Muse AI / **Veo 3** / Grok (↓ 1 lần = Veo 3). Đổi nền tảng tự đặt lại model + thời lượng (Veo 3 → 3.1 Fast 8s; Muse → 10s; Grok → 6s).
  - Model: **Omni Flash** (Home) / 3.1 Lite / 3.1 Lite LP / 3.1 Fast / 3.1 Quality (End).
  - Tỉ lệ: 16:9 (Home) / 9:16 (↓ từ 16:9) / 1:1 (End).
  - Thời lượng: 5s / 6s / 8s / **10s** (End).
- **Nhập Danh Sách Prompt** → hộp "Nhập Danh Sách Prompt Kịch Bản Cho: <dự án>": 📋 Dán Clipboard (820,272) · Dán Mẫu Thử · Hủy (846,396) · **✓ Nạp Vào Dự Án** (895,396). MỖI DÒNG = 1 CẢNH, tự bỏ chữ "Cảnh N:" đầu dòng. Nạp sẽ **THAY TOÀN BỘ** cảnh cũ của dự án, và mọi cảnh mới **kế thừa nền tảng/model/tỉ lệ/thời lượng của Cảnh 1 hiện tại** → chỉnh Cảnh 1 TRƯỚC rồi mới nạp (đã thử: ra đúng Veo 3 · Omni Flash · 16:9 · 10s cho mọi cảnh).
- Nút (+) ảnh mở hộp chọn file Windows (chọn nhiều ảnh được): gõ đường dẫn thư mục vào ô File name → Enter → gõ `"a.jpg" "b.jpg"` → Enter. Ảnh được nạp vào thư viện và gắn ngay vào cảnh.

**Mặc định dùng MACRO `tool_story_macro.py`** (07/11/2026, 20s; nhận diện: trang Kịch Bản = nút "+ Thêm Dự Án Mới" xanh ngọc (1500-1556,17-29) >15%; hộp nhập = tiêu đề sáng (640-830,242-252) >8% trắng). Quy trình tay bên dưới chỉ để hiểu / xử lý khi macro STOP.

Quy trình chuẩn (tay):
1. `python $S/tool_jobs.py export <storyboard> --lines --clip` (mỗi cảnh 1 dòng).
2. **+ Thêm Dự Án Mới** → ✏️ đổi tên = `title`.
3. Cảnh 1 mẫu: chọn nền tảng / model / tỉ lệ / thời lượng bằng phím (mặc định **Veo 3 · Omni Flash · 10s**, tỉ lệ theo storyboard).
4. **Nhập Danh Sách Prompt** → Dán Clipboard → Nạp Vào Dự Án → kiểm tra số cảnh + cài đặt từng thẻ.
5. Ảnh nhân vật / sản phẩm: (+) Ảnh đầu vào của Cảnh 1 (cảnh sau tự nối frame cuối; chỉ thêm ảnh riêng cho cảnh cần nhân vật/đồ vật mới).
6. Zoom kiểm tra nút ghi "TẠO VIDEO KỊCH BẢN (N cảnh)" đúng N → bấm. Theo dõi + lấy clip bằng `tool_jobs.py collect --wait 1800` (chạy lần lượt nên lâu hơn: ~1–3 phút/cảnh).
   Khi chạy: thanh trên hiện "Đang render Cảnh x/N…" + nút ⏹ Dừng / Đặt lại; thẻ cảnh đang chạy có viền sáng + "Đang tạo". Trước khi làm bất cứ gì trên app: đưa app lên trước bằng `python -c "import tool_macro as t; t.focus_app(topmost=False)"` (open_application hay để desktop chiếm tiêu điểm → click bị chặn).
7. Cảnh lỗi → 🔄 Tạo lại ở thẻ cảnh đó. Xong: phim ghép sẵn của tool chỉ để xem; skill vẫn dựng CapCut từ clip từng cảnh.

## 3a. Ảnh AI — tạo ảnh nhân vật / sản phẩm / khung đầu (ĐÃ HỌC GIAO DIỆN 07/11/2026)
Menu: Studio → **Ảnh AI** (~35,99). Bố cục GIỐNG Video AI: bảng "Hàng đợi Prompt" (cột NỀN TẢNG AI · CÀI ĐẶT tỉ lệ + độ nét · SỐ LƯỢNG · TÀI KHOẢN · TRẠNG THÁI), thanh trên: 📁 thư mục "ảnh" (D:\ảnh) · Tự động tải: BẬT · + Thêm prompt · **Nhập prompt** (~1333,57) · tìm kiếm. Nút chính **"Tạo ảnh N"** (~1533,23) — CÙNG chỗ nút X đóng ngăn (1553,23) → cùng quy tắc: chỉ bấm X khi thấy ngăn đang mở; tạo ảnh = bước riêng sau khi zoom kiểm tra số N.
- Bảng có thể còn prompt của anh, ĐANG TÍCH sẵn (lúc học: 4 dòng con chó/mèo/heo/bò) → khi tạo phải chỉ tích dòng mới.
- Ngăn chi tiết (đầu ngăn ghi "Cảnh N", không có ô "Prompt #N"): Nền tảng (1525,178): **ChatGPT Images / Grok / Banana / Muse AI** · Tài khoản Tự động · CÀI ĐẶT: tỉ lệ (1425,250) **16:9 / 4:3 / 1:1 / 3:4 / 9:16** · số ảnh (1477,250) · độ nét (1530,250) **Full HD / 2K / 4K** · Xoá watermark Gemini (1540,275) · Áp dụng cho mục chọn (1438,303) / tất cả (1517,303) · ẢNH THAM CHIẾU Thêm (1537,340).
- Dùng khi: cần 1 ảnh nhân vật / sản phẩm chuẩn để mọi cảnh đồng nhất, hoặc ảnh khung đầu. Ảnh tạo xong nằm trong thư viện tool (`asset-state.json`, type image, có localPath) và tự tải về D:\ảnh → dùng làm ảnh tham chiếu ở Video AI (hộp chọn ảnh, tìm theo tên) hoặc Studio Kịch Bản (+).

## 3b. Các trang khác — KHÔNG dùng trừ khi anh yêu cầu
- **Video Factory** (`Studio → Video Factory`): dây chuyền KOC thời trang / quảng cáo sản phẩm tự viết kịch bản tiếng Việt, tạo ảnh showroom (Banana Pro / Muse) rồi video (Veo 3.1 Flow 8s / Muse 10s). Skill tự viết kịch bản nên thường không dùng; chỉ dùng khi anh bảo "làm bằng Video Factory".
- **Workflows**: canvas node (Google Flow video có 2 cổng First / End frame riêng, Banana, Grok, ChatGPT, ElevenLabs…). Workflow Store: tải workflow có sẵn.
- **Image Studio**: tạo ảnh (Banana / ChatGPT Images / Muse / Grok) — dùng để làm ảnh khung đầu / nhân vật cho cảnh nếu cần.
- **TTS**: ElevenLabs lồng tiếng — skill không thêm giọng AI trừ khi anh yêu cầu.

## 4. Biết khi nào xong
`tool_jobs.py status|collect` đọc `queue-state.json`: `Pending` / `Running` (kèm %) / `Completed` / `Failed` / `Paused`. Trên giao diện: cột TRẠNG THÁI (Hàng đợi / Đang tạo / Hoàn thành / Thất bại), hoặc trang Queue. Omni Flash ~2–3 phút / cảnh, chạy song song nhiều tài khoản.

## 5. Lấy video
Không cần bấm tải: `collect` chép `asset.localPath` (`%APPDATA%\AI_VIDEO_LIBRARY_DATA\assets\<id>.mp4`, đã upscale/xoá watermark nếu bật) sang `1-canh/scene_XX.mp4`. Bản gốc vẫn nằm trong thư viện tool.

## 6. Lỗi hay gặp
- `AUTH_REQUIRED` / "Open browser account to recover" → tài khoản Veo3 hết phiên: nhờ anh vào **Browser Hub** đăng nhập lại (Claude không tự đăng nhập), rồi bấm thử lại (**Xử lý lỗi** / "Thử lại thất bại").
- `PUBLIC_ERROR_USER_QUOTA_REACHED` → tài khoản hết lượt: đổi Tài khoản sang tài khoản khác hoặc Tự động, tạo lại cảnh đó.
- "Chưa có tài khoản Veo3/Grok đăng nhập trong Browser Hub" / "Không có tài khoản khả dụng" → báo anh.
- Hết hạn bản quyền / hết hạn mức tháng ("Hạn mức tạo video còn lại trong tháng") → báo anh, không tự mua.
- Cảnh lỗi nhiều lần: chuyển nền tảng (Veo3 ↔ Muse AI) cho riêng cảnh đó.
