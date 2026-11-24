# Bộ công cụ — cách chạy

Yêu cầu: Python 3.10+, `pip install requests pillow`, FFmpeg 7+ và ffprobe (có libass) trong PATH. `SKILL_DIR` là thư mục chứa `SKILL.md`.

## Lồng tiếng (mode 2)

```bash
python SKILL_DIR/scripts/tts_elevenlabs.py --list-voices
python SKILL_DIR/scripts/tts_elevenlabs.py script.txt --voice <voice_id> -o . \
  [--model eleven_multilingual_v2] [--stability 0.5 --similarity 0.75 --style 0.3 --speed 0.95]
```
Kết quả: `voice.mp3` và `words.json` (mỗi từ có `start`, `end`, `beat` = số thứ tự đoạn). Mỗi đoạn văn cách nhau bằng dòng trống là một beat. Dòng bắt đầu bằng `#` là ghi chú, không được đọc.

Thêm `--timeline timeline.json` để sau khi lồng tiếng tự khớp lại timeline. Chạy riêng:

```bash
python SKILL_DIR/scripts/retime_timeline.py timeline.json --words words.json --voice voice.mp3
```
Mỗi mốc thời gian (beat, cảnh, graphic, `checklist.times`) được ánh xạ theo vị trí của cùng một từ trong giọng cũ và giọng mới. Graphic vẫn bám đúng từ khóa, cảnh vẫn nối liền và phủ kín video. Nếu kịch bản bị sửa nhiều (khớp dưới 80% số từ) thì script sẽ cảnh báo.

Tốc độ: `--speed` của ElevenLabs nhận khoảng 0.7–1.2. Kể chuyện nên để 0.9–1.0; video ngắn kiểu TikTok để 1.05–1.15.

## Lấy timing từ video có sẵn (mode 1)

```bash
python SKILL_DIR/scripts/transcribe_elevenlabs.py review.mp4 -o words.json [--script script.txt] [--model scribe_v1]
```
`--script`: chữ trong `words.json` sẽ lấy theo kịch bản (đúng chính tả), timing lấy theo giọng thật. Những từ phải nội suy timing sẽ có `"aligned":"interpolated"`.

## Không có API key

```bash
python SKILL_DIR/scripts/provisional_timing.py script.txt -o . [--rate 3.2] [--silence]
```
Ước lượng timing theo số âm tiết. `--silence` tạo `voice.wav` im lặng đúng độ dài để dựng thử. Timeline phải để `transcript_timing: "provisional"`.

## Phụ đề, graphic, kiểm tra, render

```bash
python SKILL_DIR/scripts/make_subs.py words.json -o build/subs --preset pop_word --font Roboto --accent "#FACC15"
python SKILL_DIR/scripts/mograph.py spec.json -o build/g1.mov      # spec = {"template":..., "data":..., "duration":3, "width":1080, "height":1920, "palette":[...], "font":"Roboto"}
python SKILL_DIR/scripts/validate_timeline.py timeline.json
python SKILL_DIR/scripts/render.py timeline.json [--preview] [--no-subs] [-o build/final.mp4]
python SKILL_DIR/scripts/export_capcut.py timeline.json [-o build/capcut_package]
```

- `render.py` tự gọi `make_subs` và `mograph`, nên thường chỉ cần validate rồi render.
- `--preview`: nửa độ phân giải, encode nhanh, dùng để duyệt.
- `--no-subs`: bản không phụ đề, để đưa vào CapCut tự thêm style.

## Đưa sang CapCut

`export_capcut.py` tạo thư mục gồm:
- `video_base.mp4`: cảnh + graphic, không phụ đề.
- `voice.*`, `subs.srt`.
- `scenes/`, `graphics/*.mov` (ProRes 4444 nền trong suốt).
- `cue_sheet.csv` + `cue_sheet.md`: thời điểm từng graphic/cảnh.

Trong CapCut: kéo `video_base.mp4` vào track chính, thêm voice, Text → Import phụ đề `subs.srt` rồi chọn template chữ. Muốn chỉnh riêng từng graphic thì tắt nó trong bản base (`render.py --no-mograph`) và đặt các file `.mov` theo cue sheet.

Định dạng project nội bộ của CapCut không công khai và hay thay đổi theo phiên bản, nên skill không ghi trực tiếp vào draft CapCut.

## Xem khung hình để QA

```bash
ffmpeg -y -ss 5.2 -i build/final.mp4 -frames:v 1 build/qa_5_2.jpg
```
Sau đó mở ảnh bằng Read để kiểm tra.
