# Bộ Skill Tự Động Hóa Làm Video & Mô Phỏng Quy Trình (AI Video Skills)

Bộ khung skill sườn gốc dùng để sản xuất video tự động bằng AI, Motion Graphic và hậu kỳ CapCut, chuyên biệt cho dòng **Video Mô Phỏng Quy Trình Xây Dựng 3D** (*"Chúc mừng bạn đã xây thành công..."*).

---

## 📂 Cấu trúc bộ skill (`.claude/skills/`)

1. **`video-mo-phong-quy-trinh`**:
   - Chuyên sản xuất video mô phỏng kỹ thuật CGI 3D kiến trúc / công trình theo trend triệu view.
   - Cơ chế cốt lõi: Khóa trạng thái thi công (`da_co` / `chua_co`) chống lỗi AI vẽ xong công trình sớm; tích hợp $\ge 2$ lớp chiều sâu (mặt cắt quét, nhìn xuyên X-ray, bóc lớp, bung rời, đường lực động).
   - Kiểm soát 12 luật vàng qua script `prep.py` và kiểm cuối độc lập qua `review_frames.py`.

2. **`ai-semantic-video-editor`**:
   - Lồng tiếng ElevenLabs tự động chia đoạn và đồng bộ khớp từng giây (`tts_parts.py`, `tts_macro.py`).
   - Phụ đề chữ vàng `story_pop` `#FACC15` nảy theo từng từ.
   - Hậu kỳ CapCut tự động: chuyển cảnh, SFX khớp từng khung hình.

3. **`tao-video`**:
   - Tự động hóa điều khiển Studio Kịch Bản / Video AI trên ứng dụng AI VIDEO LIBRARY qua macro.
   - Xử lý ghép nối 16 cảnh liên tiếp trên cùng một công trường.

4. **`video-tai-lieu`**:
   - Dựng video tài liệu, review, giải thích bằng code HTML Motion Graphic (bản đồ vệ tinh bay từ vũ trụ, thẻ hồ sơ, số liệu chạy).

5. **`video-theo-mau`**:
   - Phân tích và nhân bản nhịp điệu, visual theo video mẫu có sẵn.

---

## 🚀 Hướng dẫn mang sang máy khác sử dụng

### 1. Clone repository về máy mới
```bash
git clone <URL_REPO> "quản lý edit video"
cd "quản lý edit video"
```

### 2. Yêu cầu môi trường
- **Hệ điều hành:** Windows 10/11
- **Python:** 3.10 trở lên
- **Công cụ hỗ trợ:**
  - FFmpeg (đã thêm vào PATH)
  - Ứng dụng AI VIDEO LIBRARY (nếu tạo cảnh bằng Veo 3 / Omni qua macro)
  - CapCut Desktop (để xuất bản hậu kỳ tự động)

### 3. Tạo một dự án mới
Mọi dự án làm video sẽ được lưu trong thư mục `projects/<tên-du-an>/` (thư mục này đã được loại trừ khỏi Git để không làm nặng mã nguồn).

Ví dụ tạo video mô phỏng công trình mới:
```bash
# 1. Tạo thư mục dự án
mkdir -p projects/kim-tu-thap

# 2. Copy file mẫu kịch bản
cp .claude/skills/video-mo-phong-quy-trinh/templates/kim-tu-thap.build_sb.py projects/kim-tu-thap/build_sb.py

# 3. Lập kịch bản & kiểm duyệt
python projects/kim-tu-thap/build_sb.py
python .claude/skills/video-mo-phong-quy-trinh/scripts/prep.py projects/kim-tu-thap/storyboard.json
```
