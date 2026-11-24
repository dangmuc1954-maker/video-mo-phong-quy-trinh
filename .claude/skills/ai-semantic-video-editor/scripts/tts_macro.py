"""Macro: make the narration voice on the "Giọng đọc (TTS)" page of AI VIDEO LIBRARY (ElevenLabs in the tool).

Two phases, like tool_macro.py:
  1) python tts_macro.py projects/<slug>/storyboard.json
       app to front → TTS page → "+ Thêm prompt" (new row, only it ticked, detail panel opens)
       → paste the whole narration → close panel. Prints the next step.
     Claude then zooms (1490,14)-(1568,32): the button must read "Tạo âm thanh 1".
  2) python tts_macro.py projects/<slug>/storyboard.json --only-generate [--wait 240]
       clicks "Tạo âm thanh", waits for the new audio in the tool library (asset-state.json, matched by the
       script text), copies it to narration/voice.mp3 and runs story_voice.py --voice-file (timing + sync).

Text = scene["narration"] (or scene["dialogue"] with --from-dialogue), or --text-file. Max 1000 characters.
Voice: storyboard["narration_voice"]["voice_id"] (or --voice-id) is pasted into the panel's "Voice ID" box and loaded
with "Tải giọng" before the script is pasted. Voice ID = the one the user sends; if none, Claude picks one with
voice_catalog.py (references/voice-casting.md) and writes it to the storyboard first.
Without a voice id the row keeps the previous row's voice (macro warns). Speed/stability: inherited from the previous row.

SAFETY (see tao-video/references/tool.md, section 0a): only clicks, Ctrl+A / Ctrl+V and Esc are sent; never
F12 / Ctrl+Shift+I/J/C / Ctrl+U; no tool files are written (asset-state.json is only read). Every step checks
the screen state; wrong state → "STOP: …" with a screenshot in projects/<slug>/_macro/.
The X that closes the panel sits where the "Tạo âm thanh" button is → clicked only while the panel is open.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAO = HERE.parent.parent / "tao-video" / "scripts"
if not (TAO / "tool_macro.py").exists():
    sys.exit(f"Không thấy tao-video/scripts/tool_macro.py ở {TAO}.")
sys.path.insert(0, str(TAO))
import tool_macro as T  # noqa: E402  (helpers of the tao-video skill, not modified)

DATA = Path(os.environ.get("APPDATA", "")) / "AI_VIDEO_LIBRARY_DATA"
P = dict(nav_tts=(50, 162), add_row=(1287, 57), script_box=(1477, 100), close_panel=(1554, 23), generate=(1527, 22),
         voice_id_box=(1455, 247), load_voice=(1537, 247))
CYAN = lambda r, g, b: b > r + 25 and g > r + 15 and b > 70  # noqa: E731


def state() -> str:
    im = T.grab()
    badge = (1396, 17, 1434, 29)   # "Prompt #N" at the top of the detail panel (measured: open 0.78 dark / closed 0)
    if T.frac(im, badge, lambda r, g, b: r + g + b < 120) > 0.4 and T.frac(im, (110, 17, 200, 29), lambda r, g, b: r + g + b > 600) < 0.05:
        return "panel"
    if T.frac(im, (10, 157, 98, 168), CYAN) > 0.04 and T.frac(im, (110, 17, 200, 29), lambda r, g, b: r + g + b > 600) > 0.08:
        return "tts"                 # TTS page, no panel
    if T.frac(im, (10, 40, 98, 330), CYAN) > 0.005:
        return "menu"                # another page with the left menu
    return "other"                   # eg. workflow editor, dialog


def expect(want: str, step: str, timeout: float = 4.0) -> None:
    t0 = time.time()
    s = state()
    while time.time() - t0 < timeout:
        s = state()
        if s == want:
            return
        time.sleep(0.3)
    T.shot(f"STOP_tts_{step}")
    raise T.Stop(f"bước '{step}': cần màn hình '{want}' nhưng đang là '{s}' (xem _macro/STOP_tts_{step}.jpg)")


def ctrl(vk: int) -> None:
    if vk not in (0x41, 0x56):  # A, V only
        raise T.Stop("phím không an toàn")
    T._send(T._kb(0x11), T._kb(vk), T._kb(vk, flags=2), T._kb(0x11, flags=2))
    time.sleep(0.3)


def set_clipboard(text: str) -> None:
    tmp = Path(os.environ.get("TEMP", ".")) / "_tts_macro_clip.txt"
    tmp.write_text(text, encoding="utf-8")
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"Get-Content -Raw -Encoding UTF8 '{tmp}' | Set-Clipboard"], capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    if r.returncode:
        raise T.Stop("không ghi được clipboard")


def norm(t: str) -> str:
    return re.sub(r"\W+", "", unicodedata.normalize("NFC", t).lower())


def narration_text(a, story: dict | None) -> str:
    if a.text_file:
        lines = [l.strip() for l in Path(a.text_file).read_text(encoding="utf-8").splitlines()]
        return " ".join(l for l in lines if l and not l.startswith("#"))
    parts = []
    for sc in story["scenes"]:
        t = (sc.get("narration") or (sc.get("dialogue") if a.from_dialogue else "") or "").strip()
        if not t:
            sys.exit(f"Cảnh {sc['id']} chưa có 'narration'.")
        parts.append(t)
    return " ".join(parts)


def set_voice(voice_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9]{16,32}", voice_id):
        raise T.Stop(f"voice_id không hợp lệ: {voice_id}")
    T.click(*P["voice_id_box"], wait=0.3)
    ctrl(0x41)
    set_clipboard(voice_id)
    ctrl(0x56)
    time.sleep(0.3)
    T.click(*P["load_voice"], wait=2.5)
    expect("panel", "tai_giong")
    T.shot("tts_0_voice")


def prepare(text: str, job: Path, voice_id: str | None = None) -> None:
    T.focus_app(topmost=True)
    try:
        s = state()
        if s == "panel":                       # a panel left open: close it first
            T.click(*P["close_panel"], wait=0.8)
            s = state()
        if s in ("menu", "tts"):
            T.click(*P["nav_tts"], wait=1.2)
        expect("tts", "trang_tts")
        T.click(*P["add_row"], wait=1.0)
        expect("panel", "them_prompt")
        if voice_id:
            set_voice(voice_id)
        T.click(*P["script_box"], wait=0.4)
        ctrl(0x41)
        set_clipboard(text)
        ctrl(0x56)
        time.sleep(0.6)
        T.shot("tts_1_pasted")
        T.click(*P["close_panel"], wait=0.8)
        expect("tts", "dong_ngan")
        T.shot("tts_2_ready")
    finally:
        T.release_topmost()
    job.write_text(json.dumps({"text": text, "voice_id": voice_id, "prepared_at": time.time()}, ensure_ascii=False), encoding="utf-8")
    print(f"ĐÃ NHẬP kịch bản vào dòng TTS mới" + (f", giọng {voice_id}." if voice_id else " (giọng của dòng trước)."))
    if voice_id:
        print("Claude xem _macro/tts_0_voice.jpg: ô Voice ID phải ghi đúng id và có chữ 'saved'.")
    print("Tiếp: Claude zoom (1490,14)-(1568,32), nút phải ghi 'Tạo âm thanh 1', rồi chạy lại với --only-generate.")


def find_audio(text: str, since: float):
    from datetime import datetime
    a = json.loads((DATA / "asset-state.json").read_text(encoding="utf-8"))
    key = norm(text)[:200]
    best = None
    for x in a.get("assets", []):
        if x.get("type") != "audio" or not x.get("localPath"):
            continue
        try:
            ts = datetime.fromisoformat(x["createdAt"].replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        if ts >= since - 5 and norm(x.get("prompt", ""))[:200] == key and Path(x["localPath"]).exists():
            if best is None or ts > best[0]:
                best = (ts, x)
    return best[1] if best else None


def generate(text: str, out_dir: Path, wait: int) -> Path:
    T.focus_app(topmost=True)
    try:
        expect("tts", "truoc_khi_tao")         # never click (1527,22) while the panel is open (it would be X)
        t0 = time.time()
        T.click(*P["generate"], wait=1.0)
        T.shot("tts_3_generate")
    finally:
        T.release_topmost()
    print("Đã bấm Tạo âm thanh, đang chờ file giọng…")
    while time.time() - t0 < wait:
        x = find_audio(text, t0)
        if x:
            out = out_dir / "voice.mp3"
            shutil.copy2(x["localPath"], out)
            print(f"Xong: {x.get('provider', 'ElevenLabs')} → {out} ({x.get('bytes', 0) // 1024} KB)")
            return out
        time.sleep(2)
    raise T.Stop(f"chờ {wait}s chưa thấy file giọng — Claude chụp màn hình trang TTS xem trạng thái (Thất bại / hết lượt?)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard", nargs="?")
    ap.add_argument("--text-file")
    ap.add_argument("--from-dialogue", action="store_true")
    ap.add_argument("--only-generate", action="store_true")
    ap.add_argument("--auto", action="store_true",
                    help="chạy liền: nhập → OCR kiểm nút 'Tạo âm thanh 1' → tạo → lấy file → đồng bộ (không cần Claude chụp màn hình)")
    ap.add_argument("--voice-id", help="ghi đè storyboard.narration_voice.voice_id")
    ap.add_argument("--wait", type=int, default=240)
    ap.add_argument("--no-sync", action="store_true", help="chỉ lấy file giọng, không chạy story_voice.py")
    a = ap.parse_args()
    if not a.storyboard and not a.text_file:
        sys.exit("Cần storyboard.json hoặc --text-file.")

    sp = Path(a.storyboard).resolve() if a.storyboard else None
    story = json.loads(sp.read_text(encoding="utf-8")) if sp else None
    proj = sp.parent if sp else Path(a.text_file).resolve().parent
    out_dir = proj / "narration"
    out_dir.mkdir(exist_ok=True)
    T.SHOTS = str(proj / "_macro")
    os.makedirs(T.SHOTS, exist_ok=True)
    job = out_dir / "_tts_job.json"

    try:
        if not a.only_generate:
            text = narration_text(a, story)
            if len(text) > 1000:
                sys.exit(f"Lời kể {len(text)} ký tự, quá 1000 ký tự của một dòng TTS. Rút gọn hoặc chia video.")
            vid = a.voice_id or ((story or {}).get("narration_voice") or {}).get("voice_id")
            if not vid:
                print("CẢNH BÁO: chưa có voice ID (storyboard.narration_voice.voice_id / --voice-id), "
                      "dùng giọng của dòng trước. Nếu anh không nói dùng giọng cũ thì chọn giọng theo references/voice-casting.md.")
            prepare(text, job, vid)
            if not a.auto:
                return
            sys.path.insert(0, str(HERE))
            from screen_ocr import button_shows
            T.focus_app(topmost=True)
            try:
                time.sleep(0.6)
                ok, seen = button_shows((1490, 14, 1568, 32), 1, save=str(Path(T.SHOTS) / "ocr_tts_button.png"))
            finally:
                T.release_topmost()
            print(f"OCR nút: {seen!r} → {'KHỚP' if ok else 'KHÔNG KHỚP'}")
            if not ok:
                raise T.Stop("nút không ghi 'Tạo âm thanh 1' (có dòng lạ đang tích?) — không bấm tạo; xem _macro/ocr_tts_button.png")
        if a.auto:
            voice = generate(text, out_dir, a.wait)
        else:
            if not job.exists():
                sys.exit("Chưa chạy bước nhập (không có narration/_tts_job.json).")
            text = json.loads(job.read_text(encoding="utf-8"))["text"]
            voice = generate(text, out_dir, a.wait)
    except T.Stop as e:
        print(f"STOP: {e}")
        sys.exit(2)

    if sp and not a.no_sync:
        cmd = [sys.executable, str(HERE / "story_voice.py"), str(sp), "--voice-file", str(voice)]
        if a.from_dialogue:
            cmd.append("--from-dialogue")
        sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
