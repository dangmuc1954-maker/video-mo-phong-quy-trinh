# AI Semantic Video Editor — Claude Code skill (tiếng Việt)

Skill dựng video có giọng nói tiếng Việt, gồm 2 mode:

1. **KOC_REVIEW**: đưa video KOC/reviewer vào. Claude lấy timing từng từ, sửa chữ theo kịch bản, chèn motion graphic (số chạy, biểu đồ, danh sách công dụng, chú thích sản phẩm, so sánh, chữ chốt) đúng lúc nói từ khóa, và làm phụ đề tiếng Việt với 6 style.
2. **STORYTELLING**: đưa ý tưởng hoặc đạo lý vào. Claude viết kịch bản, chia cảnh, chọn cảnh hoặc ẩn dụ khớp từng câu, viết prompt ảnh/video, lồng tiếng ElevenLabs, rồi ghép video (chuyển động máy, graphic, phụ đề, nhạc nền tự giảm khi có giọng).

Xuất ra video MP4 hoàn chỉnh bằng FFmpeg, hoặc gói CapCut (video nền, voice, `.srt`, graphic nền trong suốt, bảng cue) để anh tự chỉnh tiếp.

## Cài đặt

1. Chép cả thư mục `ai-semantic-video-editor` vào `~/.claude/skills/` (dùng cho mọi dự án), hoặc vào `<dự-án>/.claude/skills/`.
2. Cài thư viện: `pip install requests pillow`. Cần FFmpeg 7+ có libass trong PATH.
3. Lồng tiếng và nhận dạng giọng nói: tạo file `.env` trong thư mục dự án với dòng `ELEVENLABS_API_KEY=...`.
4. (Tùy chọn) Bỏ font `.ttf` riêng (ví dụ Be Vietnam Pro) vào `ai-semantic-video-editor/assets/fonts/`.

## Cách dùng

- *"Dùng skill ai-semantic-video-editor, mode KOC_REVIEW. Video `review.mp4`, kịch bản `script.txt`. Phụ đề pop_word, chèn graphic số liệu và công dụng đúng lúc nói."*
- *"Dùng skill ai-semantic-video-editor, mode STORYTELLING. Làm video 45 giây về sự kiên trì, phong cách hoạt hình 3D, giọng nam trầm ấm."*

Ví dụ hoàn chỉnh ở `examples/dao-vang/` (kịch bản, timeline, prompt ảnh, bản preview). Bản này dùng timing tạm tính và ảnh giữ chỗ.

## Giới hạn

- Skill không tự tạo ảnh/video AI. Nó xuất prompt vào `prompts.md`, anh tạo ảnh bằng công cụ mình dùng rồi lưu thành `assets/<id>.png` hoặc `.mp4`. Khi chưa có ảnh, video sẽ hiện thẻ giữ chỗ.
- Định dạng project nội bộ của CapCut không công khai, nên skill xuất gói file kèm bảng cue thay vì ghi thẳng vào draft CapCut.
- Không có API key thì timing chỉ là ước lượng (`provisional_timing.py`).
