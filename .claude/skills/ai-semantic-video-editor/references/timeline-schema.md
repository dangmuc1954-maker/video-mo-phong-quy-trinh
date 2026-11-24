# Timeline contract (JSON v2)

`render.py`, `export_capcut.py` và `validate_timeline.py` đều đọc file này. Mọi đường dẫn file tính tương đối so với thư mục chứa `timeline.json`. Thời gian tính bằng giây từ đầu audio giọng nói, `end` không bao gồm (exclusive).

```jsonc
{
  "version": "2.0",
  "mode": "KOC_REVIEW" | "STORYTELLING",
  "project": {
    "title": "…",
    "language": "vi",
    "fps": 30, "width": 1080, "height": 1920,
    "duration_seconds": 42.5,          // = độ dài voice (mode 2) hoặc video gốc (mode 1)
    "voice_audio": "voice.mp3",        // mode 2 bắt buộc; mode 1 có thể null (dùng audio của video)
    "source_video": null,              // mode 1 bắt buộc
    "bgm": "assets/bgm.mp3" | null,
    "bgm_volume": 0.18,                // 0–1, tự giảm thêm khi có giọng nói (ducking)
    "transcript_timing": "verified" | "provisional"
  },
  "style_bible": {
    "palette": ["#0F172A", "#FFFFFF", "#FACC15"],   // nền thẻ, chữ, màu nhấn
    "font": "Roboto",                               // tên font; render tự tìm file .ttf
    "subtitle_preset": "pop_word",                  // clean|box|karaoke|pop_word|keyword|cinematic
    "subtitle_uppercase": false,
    "motion_style": "clean_eased",
    "pacing": "moderate",
    "character_bible": { "co_gai": "nữ 17 tuổi, tóc đen dài buộc đuôi ngựa, áo dài trắng…" },  // mode 2
    "visual_style": "cinematic 3D animation, warm light, …"                                   // mode 2: hậu tố chung cho mọi prompt
  },
  "words": [ { "id": "w1", "text": "Ngày", "start": 0.12, "end": 0.38, "confidence": 0.98, "beat": 0 } ],
  "beats": [ {
    "id": "b1", "start": 0.0, "end": 4.2,
    "spoken_text": "…", "meaning": "…", "emotional_intent": "…",
    "narrative_function": "hook|setup|conflict|turning_point|realization|lesson|cta",   // mode 2
    "visual_type": "speaker_only|mograph|scene|broll|product_highlight|kinetic_text",
    "rationale": "Vì sao hình ảnh này khớp lời nói",
    "asset_ids": ["s1"], "visual_cue_word_ids": ["w3"],
    "keywords": ["kiên trì"]          // tô màu trong preset phụ đề `keyword`
  } ],
  "assets": [ {
    "id": "s1", "kind": "image|video|audio",
    "file": "assets/s1.png" | null,
    "prompt": "prompt tạo ảnh/video (mode 2)",
    "license": "AI-generated (Midjourney) / stock XYZ / user-owned",
    "status": "ready|missing|needs_verification"
  } ],
  "layers": [
    // Mode 2: track cảnh nền. Các cảnh phải liên tiếp và phủ kín 0 → duration.
    { "id": "L1", "type": "scene", "start": 0.0, "end": 4.2, "asset_id": "s1",
      "motion": "push_in|pull_out|pan_left|pan_right|pan_up|pan_down|static", "beat_id": "b1" },

    // Motion graphic (cả hai mode). render.py tự gọi mograph.py.
    { "id": "G1", "type": "mograph", "start": 5.1, "end": 8.0, "beat_id": "b2",
      "template": "counter|bar_chart|checklist|callout|compare|kinetic_text",
      "anchor": "top|center|upper_left|upper_right|lower_third|middle_left|middle_right",
      "data": { … xem references/mode1-koc-review.md … } },

    // Ảnh/video phủ lên (logo, ảnh sản phẩm PNG trong suốt, B-roll khung nhỏ)
    { "id": "O1", "type": "overlay", "start": 9.0, "end": 12.0, "asset_id": "p1",
      "x": 0.5, "y": 0.3, "scale": 0.45, "beat_id": "b3" },   // x,y = tâm, tính theo tỉ lệ khung

    // Mode 1: B-roll full khung thay tạm người nói (giữ audio gốc)
    { "id": "R1", "type": "broll", "start": 14.0, "end": 16.5, "asset_id": "v2", "beat_id": "b5" }
  ],
  "qa": { "unverified_claims": [], "missing_assets": [], "subtitle_alignment_status": "verified|provisional",
          "visual_alignment_status": "planned|rendered|checked", "notes": [] }
}
```

## Quy tắc (validate_timeline.py kiểm tra)

- `0 <= start < end <= duration_seconds` cho mọi beat, layer và word.
- `words` theo thứ tự thời gian, không chồng lấn quá 0.05s.
- `visual_cue_word_ids` phải trỏ tới `words.id` có thật; `asset_id` và `beat_id` phải tồn tại.
- Mode 2: các layer `scene` nối liền (khe hở ≤ 0.05s) và phủ toàn bộ thời lượng.
- Mode 1: phải có `source_video`.
- Asset `status: ready` thì file phải tồn tại. Asset `missing` sẽ được render thành placeholder.
- `bar_chart` / `counter` phải có `data.source`, hoặc `data.illustrative: true` (khi đó tự gắn nhãn "Minh họa giả định").
