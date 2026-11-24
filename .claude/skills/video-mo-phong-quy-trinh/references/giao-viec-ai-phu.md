# Mẫu giao việc cho AI phụ (đã chạy thử 13/11/2026 với Sonnet 5.5 — tiết kiệm token, chạy nền, báo giờ)

Nguyên tắc: AI phụ chỉ làm việc KHÔNG cần giao diện (viết file, soát), chạy nền (`run_in_background`), brief ngắn nêu rõ file cần đọc + file cần ghi + yêu cầu báo giờ (`date +%H:%M:%S`) để đo tốc độ. Việc điều khiển tool / CapCut luôn do AI chính (một chuột).

## A. AI BIÊN KỊCH (Sonnet, ~45 giây, ~80k token)
Giao cùng lúc với việc tạo ảnh nhân vật (Ảnh AI) để không chờ nhau:
```
Agent(subagent_type="general-purpose", model="sonnet", run_in_background=true, prompt="""
Working directory: <thư mục dự án>. Bạn là AI BIÊN KỊCH. Chỉ viết file, KHÔNG dùng tool AI VIDEO LIBRARY/TTS/CapCut/computer-use.
Đọc: CLAUDE.md, .claude/skills/<skill>/SKILL.md (+ references liên quan), template storyboard.
NHIỆM VỤ: viết projects/<slug>/storyboard.json cho video <chủ đề, thông điệp, cảm xúc, đường cảm xúc>.
Ràng buộc: <số cảnh × giây, tỉ lệ, type, style>; nhân vật duy nhất copy NGUYÊN VĂN <câu mô tả>; lời kể vào "narration" (24–32 âm tiết/cảnh, tổng ≤ 900 ký tự), viết theo giong-ke-hay.md;
mỗi cảnh có id, clip, setting, characters, beats/action, camera, narration, chain ("A"/"B"…); cảnh đầu mỗi chuỗi có reference_images; cảnh còn lại continue_from_previous.
Cuối: chạy make_prompts.py. Báo: logline, bảng # | lời kể | hình, tổng ký tự, giờ bắt đầu/kết thúc.""")
```
Kết quả thử: kịch bản 8 cảnh ~45s; chất lượng đạt nếu brief nêu rõ chất giọng + ràng buộc.

## B. AI SOÁT ĐỘC LẬP (Sonnet, ~25 giây, ~65k token)
Sau khi có `review_frames.py` (hoặc review_sheet.py cho video tài liệu):
```
Agent(model="sonnet", run_in_background=true, prompt="""
Bạn là AI KIỂM CUỐI độc lập (không biết quá trình làm). Chỉ đọc file và trích khung ffmpeg.
Đọc <projects/slug/render/review/brief.md> + sheet_*.jpg; video <đường dẫn>.
Soát: hình đúng lời từng cảnh (đặc biệt cảnh có thời tiết/hành động mạnh); nhân vật giữ thiết kế mọi cảnh; mảng xám/lỗi render/chữ lạ/logo; sub đúng chữ đủ dấu không đè; lời kể hay/đúng đường cảm xúc/câu chốt; chỗ nhạt.
Ghi <render/review_report.md> (lỗi chắc kèm cảnh/giây; mục cần xem; dòng cuối 'KẾT LUẬN: ĐẠT' hoặc 'KẾT LUẬN: CẦN SỬA'). Báo giờ.""")
```
Thực tế: agent soát bắt được lỗi AI chính bỏ sót (cảnh 4 lời kể mưa mà hình nắng; mảng xám ở cảnh mặt cắt). Luôn giao soát SONG SONG với xuất CapCut.
