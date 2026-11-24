"""Kiểm tra chất lượng các cảnh và lập kế hoạch cắt tự động.

python analyze_clips.py projects/<slug>/storyboard.json

Đọc clip trong projects/<slug>/1-canh, ghi ra:
  - projects/<slug>/edit_plan.json: mỗi cảnh có trim_start / trim_end (giây), drop (bỏ cảnh), ghi chú
  - projects/<slug>/1-canh/_review.jpg: ảnh tổng hợp 4 khung/cảnh để Claude xem bằng mắt

Phát hiện được:
  * đứng hình ở đầu/cuối clip (freezedetect) → cắt bỏ
  * đứng hình giữa clip > 1s → ghi chú để xem lại
  * giật/nhảy cảnh bất thường trong clip (scene cut) → ghi chú; nếu ở sát đầu/cuối thì cắt
  * cảnh nối tiếp: khung đầu trùng khung cuối cảnh trước → cắt 0.2s đầu cho khỏi khựng
  * hai cảnh trùng nhau (gần như cùng hình ảnh) → drop cảnh sau
"""
import json
import os
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
FF = shutil.which("ffmpeg")
FP = shutil.which("ffprobe")


def run(args):
    return subprocess.run(args, capture_output=True, text=True, errors="ignore")


def duration(p):
    return float(run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).stdout.strip())


def freezes(p):
    err = run([FF, "-hide_banner", "-nostats", "-i", p, "-vf", "freezedetect=n=0.003:d=0.35", "-an", "-f", "null", "-"]).stderr
    st = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", err)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def cuts(p):
    err = run([FF, "-hide_banner", "-nostats", "-i", p, "-vf", "select='gt(scene,0.45)',showinfo", "-an", "-f", "null", "-"]).stderr
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", err)]


def signature(p, at):
    """Khung hình nhỏ 32x18 xám tại thời điểm `at` → list byte."""
    out = subprocess.run([FF, "-v", "error", "-ss", str(at), "-i", p, "-frames:v", "1", "-vf", "scale=32:18,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    return out


def diff(a, b):
    if not a or not b or len(a) != len(b):
        return 255
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def main(story_path):
    base = os.path.dirname(os.path.abspath(story_path))
    clips_dir = os.path.join(base, "1-canh")
    story = json.load(open(story_path, encoding="utf-8"))
    plan, sigs, prev_last = {}, {}, None
    clip_of = {str(sc["id"]): sc["clip"] for sc in story["scenes"]}

    for sc in story["scenes"]:
        sid = str(sc["id"])
        p = os.path.join(clips_dir, sc["clip"])
        d = duration(p)
        item = {"trim_start": 0.0, "trim_end": 0.0, "drop": False, "notes": []}

        for s, e in freezes(p):
            e = d if e is None else e
            if s <= 0.05:
                item["trim_start"] = max(item["trim_start"], round(e, 2)); item["notes"].append(f"đứng hình đầu {e:.1f}s → cắt")
            elif e >= d - 0.05:
                item["trim_end"] = max(item["trim_end"], round(d - s, 2)); item["notes"].append(f"đứng hình cuối {d - s:.1f}s → cắt")
            elif e - s > 1.0:
                item["notes"].append(f"đứng hình giữa {s:.1f}–{e:.1f}s (xem lại)")

        for c in cuts(p):
            if c < 0.8:
                item["trim_start"] = max(item["trim_start"], round(c, 2)); item["notes"].append(f"giật hình ở {c:.1f}s đầu → cắt")
            elif c > d - 0.8:
                item["trim_end"] = max(item["trim_end"], round(d - c, 2)); item["notes"].append(f"giật hình ở {c:.1f}s cuối → cắt")
            else:
                item["notes"].append(f"nhảy cảnh trong clip ở {c:.1f}s (xem lại)")

        # đoạn ì (gần như không chuyển động) ở đầu/cuối > 1.5s → cắt bớt, giữ lại 1s
        step = 0.5
        frames = [signature(p, t * step) for t in range(int(d / step))]
        raw = [diff(a, b) for a, b in zip(frames, frames[1:])]
        motion = [sum(raw[max(0, i - 1):i + 2]) / len(raw[max(0, i - 1):i + 2]) for i in range(len(raw))]  # làm mượt
        still = 3.0
        head = next((i for i, m in enumerate(motion) if m > still), len(motion)) * step
        tail = next((i for i, m in enumerate(reversed(motion)) if m > still), len(motion)) * step
        if head > 1.5 and not sc.get("continue_from_previous"):
            item["trim_start"] = max(item["trim_start"], round(min(head - 1.0, 2.5), 2)); item["notes"].append(f"đầu clip ì {head:.1f}s → cắt bớt")
        next_sc = next((s for s in story["scenes"] if s["id"] == sc["id"] + 1), None)
        if tail > 1.5 and not (next_sc and next_sc.get("continue_from_previous")):
            item["trim_end"] = max(item["trim_end"], round(min(tail - 1.0, 2.5), 2)); item["notes"].append(f"cuối clip ì {tail:.1f}s → cắt bớt")

        first = signature(p, 0.05)
        if sc.get("continue_from_previous") and prev_last is not None and diff(first, prev_last) < 6:
            item["trim_start"] = max(item["trim_start"], 0.2); item["notes"].append("khung đầu trùng cảnh trước → cắt 0.2s cho mượt")

        sig = [signature(p, d * k / 5) for k in range(1, 5)]
        for other, osig in sigs.items():
            if clip_of.get(other) == sc["clip"]:
                continue  # cùng 1 clip, cắt nhiều đoạn (keep) → không tính là trùng
            if sum(diff(a, b) for a, b in zip(sig, osig)) / 4 < 5:
                item["drop"] = True; item["notes"].append(f"trùng gần như y hệt cảnh {other} → bỏ")
                break
        sigs[sid] = sig
        prev_last = signature(p, max(d - 0.1, 0))

        if d - item["trim_start"] - item["trim_end"] < 3:
            item["notes"].append("còn quá ngắn sau khi cắt → giữ nguyên, nên tạo lại cảnh")
            item["trim_start"] = item["trim_end"] = 0.0
        plan[sid] = item
        print(f"Cảnh {sid}: {d:.1f}s  cắt đầu {item['trim_start']}s, cắt cuối {item['trim_end']}s"
              + ("  [BỎ]" if item["drop"] else "") + ("  | " + "; ".join(item["notes"]) if item["notes"] else "  | ổn"))

    json.dump(plan, open(os.path.join(base, "edit_plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ảnh tổng hợp: mỗi cảnh 1 hàng 4 khung
    rows = []
    for sc in story["scenes"]:
        p = os.path.join(clips_dir, sc["clip"])
        d = duration(p)
        row = os.path.join(clips_dir, f"_row_{sc['id']}.jpg")
        run([FF, "-y", "-v", "error", "-i", p, "-vf",
             f"fps=4/{d},scale=320:-2,drawtext=text='{sc['id']}':x=8:y=8:fontsize=28:fontcolor=yellow:fontfile=C\\\\:/Windows/Fonts/arial.ttf,tile=4x1",
             "-frames:v", "1", row])
        rows.append(row)
    inputs = sum([["-i", r] for r in rows if os.path.exists(r)], [])
    n = len(inputs) // 2
    run([FF, "-y", "-v", "error", *inputs, "-filter_complex", "".join(f"[{i}]" for i in range(n)) + f"vstack={n}",
         os.path.join(clips_dir, "_review.jpg")])
    for r in rows:
        if os.path.exists(r):
            os.remove(r)
    print(f"Kế hoạch: {os.path.join(base, 'edit_plan.json')}\nẢnh duyệt: {os.path.join(clips_dir, '_review.jpg')}")


if __name__ == "__main__":
    main(sys.argv[1])
