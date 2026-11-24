"""Ghép prompt Muse cho từng cảnh từ storyboard.json, cho MỌI loại video.

python make_prompts.py projects/<slug>/storyboard.json

Storyboard (xem templates/):
  "type":      animation | realistic | product | tips | nature | review | timelapse | ...  (chỉ để chọn mặc định)
  "aspect":    "16:9" | "9:16" | "1:1"
  "style":     1 câu phong cách hình ảnh cố định
  "subjects":  {"ten": "mô tả cố định"}  ← nhân vật / người mẫu / sản phẩm / con vật / địa điểm
               (trường cũ "characters" vẫn đọc được)
  "settings":  {"ten": "mô tả bối cảnh"}
  "lock":      câu khoá đồng nhất riêng (mặc định theo type)
  "negative":  câu cấm (mặc định theo type)
Mỗi cảnh:
  "action" (1 câu) HOẶC "beats": [["0-2s","..."], ["2-5s","..."]]  ← diễn biến theo giây cho cảnh phức tạp
  "subjects"/"characters", "setting", "camera", "dialogue", "seconds" (mặc định 10)
  "reference_images": ["ref/ao-khoac.jpg"]  ← ảnh đính kèm khi gửi Muse (image-to-video)
  "first_last": ["ref/dau.jpg","ref/cuoi.jpg"] ← chế độ khung hình đầu/cuối của Muse
  "continue_from_previous": true
  "prompt_override": "..." ← dùng nguyên prompt anh tự viết
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_LOCK = {
    "realistic": "Preserve the exact same face, hairstyle, body proportions, clothing design, logos, colors, lighting and background as the reference. Accurate hands and fingers, natural fabric and body physics, smooth continuous motion.",
    "product": "Keep the product shape, colors, label, logo and proportions exactly the same in every frame. Product stays sharp and clearly visible.",
    "animation": "Keep character designs exactly as described in every frame.",
}
DEFAULT_NEG = {
    "realistic": "No face morphing, no identity drift, no extra fingers, no duplicated limbs, no clothing transformation, no changing logos, no sudden pose changes, no camera shake, no text, no watermark.",
    "product": "No deformed product, no changing label or logo, no extra products, no text overlays, no watermark.",
    "_": "No text, no subtitles, no watermark, no logos.",
}

path = sys.argv[1]
s = json.load(open(path, encoding="utf-8"))
typ = s.get("type", "animation")
aspect = s.get("aspect", "16:9")
orient = {"9:16": "vertical", "1:1": "square"}.get(aspect, "landscape")
subjects = s.get("subjects") or s.get("characters") or {}
lock = s.get("lock", DEFAULT_LOCK.get(typ, DEFAULT_LOCK["animation"] if subjects else ""))
neg = s.get("negative", DEFAULT_NEG.get(typ, DEFAULT_NEG["_"]))

for sc in s["scenes"]:
    if sc.get("prompt_override"):
        sc["prompt"] = sc["prompt_override"]
    else:
        who = sc.get("subjects") or sc.get("characters") or list(subjects)
        sec = sc.get("seconds", 10)
        p = []
        if sc.get("reference_images"):
            p.append("Use the attached image(s) as the exact visual reference.")
        if sc.get("first_last"):
            p.append("Image 1 is the exact first frame, image 2 is the exact last frame." if len(sc["first_last"]) > 1
                     else "The attached image is the exact first frame; start the video from it.")
        if sc.get("continue_from_previous"):
            p.append("Continue seamlessly from the last frame of the previous video.")
        p.append(f"Create a {sec}-second video, {aspect} {orient}, single continuous shot.")
        if s.get("style"):
            p.append(f"Style: {s['style']}.")
        if who and subjects:
            p.append("Subjects: " + " ".join(f"{n.upper()} = {subjects[n]}." for n in who if n in subjects))
        st = sc.get("setting")
        if st:
            p.append(f"Setting: {s.get('settings', {}).get(st, st)}.")
        if sc.get("beats"):
            p.append("Action timeline: " + " ".join(f"{t}: {a}" for t, a in sc["beats"]))
        else:
            p.append(f"Action: {sc['action']}")
        p.append(f"Camera: {sc.get('camera', 'medium shot, eye level, smooth')}.")
        if sc.get("dialogue"):
            if s.get("narration"):  # giọng kể ngoài khung hình, nhân vật không mở miệng
                p.append(f"Voice-over narration (off-screen narrator, the character does not speak), spoken exactly in Vietnamese: \"{sc['dialogue']}\"")
            else:
                p.append(f"Dialogue (spoken aloud, clear voice): {sc['dialogue']}")
        if lock:
            p.append(f"Consistency: {lock}")
        p.append(f"Negative: {neg}")
        sc["prompt"] = " ".join(p)
    extra = ""
    if sc.get("reference_images"):
        extra = f"  [đính kèm: {', '.join(sc['reference_images'])}]"
    if sc.get("first_last"):
        fl = sc["first_last"]
        extra = f"  [chế độ khung hình: {fl[0]}" + (f" → {fl[1]}]" if len(fl) > 1 else " (chỉ khung đầu)]")
    print(f"--- Cảnh {sc['id']}{extra} ---\n{sc['prompt']}\n")

json.dump(s, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
