"""Chế độ TOOL (AI VIDEO LIBRARY): xuất prompt, theo dõi tiến độ, lấy clip — CHỈ ĐỌC dữ liệu của tool.

python tool_jobs.py export  projects/<slug>/storyboard.json [--clip] [--lines] [--refs]
    → tool_import.txt (mỗi prompt cách 1 dòng trống, dùng cho Video AI → Nhập prompt)
    → --refs : chép ảnh tham chiếu đầu tiên của mỗi cảnh thành tool_refs/canh<N>.<đuôi>
               (hộp Nhập prompt, chế độ "Theo tên cảnh" tự ghép ảnh canhN vào Cảnh N)
    → --lines: mỗi cảnh 1 dòng (dùng cho Studio Kịch Bản → Nhập Danh Sách Prompt)
    → --clip : chép luôn vào clipboard để dán
python tool_jobs.py status  projects/<slug>/storyboard.json
python tool_jobs.py collect projects/<slug>/storyboard.json [--wait 900]
    → chép video cảnh đã xong vào 1-canh/scene_XX.mp4, ghi tool_jobs.json.
      --wait N: chờ tối đa N giây cho tới khi đủ cảnh (kiểm tra mỗi 15s).

Tool lưu trạng thái ở %APPDATA%/AI_VIDEO_LIBRARY_DATA (queue-state.json, asset-state.json).
Script không bao giờ ghi vào thư mục đó.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
DATA = os.path.join(os.environ.get("APPDATA", ""), "AI_VIDEO_LIBRARY_DATA")


def norm(t):
    return re.sub(r"\s+", " ", (t or "")).strip().lower()


def load(name):
    p = os.path.join(DATA, name)
    for _ in range(5):  # tool có thể đang ghi file
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            time.sleep(0.5)
    sys.exit(f"Không đọc được {p}")


def scene_prompts(sb):
    out = []
    for sc in sb["scenes"]:
        p = sc.get("prompt") or sc.get("prompt_override")
        if not p:
            sys.exit(f"Cảnh {sc['id']} chưa có prompt — chạy make_prompts.py trước.")
        out.append((sc, p))
    return out


def find_jobs(sb):
    jobs = [j for j in load("queue-state.json").get("jobs", []) if j.get("type") == "Video"]
    jobs.sort(key=lambda j: j.get("createdAt", ""), reverse=True)  # mới nhất trước
    res = {}
    for sc, p in scene_prompts(sb):
        # So cả prompt: các cảnh cùng style/nhân vật thường trùng hàng trăm ký tự đầu.
        key = norm(p)
        for j in jobs:
            jp = norm(j.get("payload", {}).get("prompt") or j.get("title"))
            if key and (jp == key or key in jp):
                res[str(sc["id"])] = j
                break
    return res


def asset_for(job, assets):
    ids = [a.get("url", "").rsplit("/", 1)[-1] for a in (job.get("result") or {}).get("assets", []) if a.get("type") == "video"]
    for a in assets:
        if a.get("type") == "video" and (a.get("jobId") == job["id"] or a.get("id") in ids):
            if a.get("localPath") and os.path.isfile(a["localPath"]):
                return a
    return None


def cmd_export(a, sb, proj):
    items = [p for _, p in scene_prompts(sb)]
    text = ("\n".join(re.sub(r"\s+", " ", p) for p in items) if a.lines
            else "\n\n".join(p.strip() for p in items))
    out = os.path.join(proj, "tool_import_lines.txt" if a.lines else "tool_import.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Đã ghi {len(items)} prompt → {out}")
    if a.refs:
        rd = os.path.join(proj, "tool_refs")
        shutil.rmtree(rd, ignore_errors=True)
        os.makedirs(rd)
        n = 0
        for i, (sc, _) in enumerate(scene_prompts(sb), 1):
            imgs = sc.get("reference_images") or sc.get("first_last") or []
            if isinstance(imgs, str):
                imgs = [imgs]
            if imgs:
                src = imgs[0] if os.path.isabs(imgs[0]) else os.path.join(proj, imgs[0])
                shutil.copy2(src, os.path.join(rd, f"canh{i}{os.path.splitext(src)[1].lower()}"))
                n += 1
                if len(imgs) > 1:
                    print(f"  Cảnh {i}: có {len(imgs)} ảnh — hộp Nhập chỉ ghép 1 ảnh, thêm ảnh còn lại bằng tay ở ngăn chi tiết.")
        print(f"Đã chép {n} ảnh tham chiếu → {rd}")
    if a.clip:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"Get-Content -Raw -Encoding UTF8 '{out}' | Set-Clipboard"], check=True)
        print("Đã chép vào clipboard.")


def report(sb, jobs, assets=None):
    rows, done = [], 0
    for sc, _ in scene_prompts(sb):
        j = jobs.get(str(sc["id"]))
        if not j:
            rows.append((sc["id"], "CHƯA GỬI", "", ""))
            continue
        st = j.get("status")
        info = j.get("statusText") or ""
        code = j.get("providerErrorCode")
        if not code and j.get("error"):
            m = re.search(r"PUBLIC_ERROR_[A-Z_]+|[A-Z]{4,}_[A-Z_]+", j["error"])
            code = m.group(0) if m else " ".join(j["error"][:60].split())
        if code:
            info = f"{code} — {info} (lần {j.get('attempts', '?')}/{j.get('maxAttempts', '?')})"
        if st == "Completed":
            done += 1
        rows.append((sc["id"], st, f"{j.get('progress', '')}%", f"{j.get('provider')}/{j.get('payload', {}).get('model')} · {info}"[:110]))
    for r in rows:
        print(f"Cảnh {r[0]:>2} | {r[1]:<10} | {r[2]:>4} | {r[3]}")
    print(f"Xong {done}/{len(rows)}")
    return done, len(rows)


def cmd_status(a, sb, proj):
    report(sb, find_jobs(sb))


def cmd_collect(a, sb, proj):
    clips = os.path.join(proj, "1-canh")
    os.makedirs(clips, exist_ok=True)
    state_p = os.path.join(proj, "tool_jobs.json")
    state = json.load(open(state_p, encoding="utf-8")) if os.path.isfile(state_p) else {}
    deadline = time.time() + a.wait
    while True:
        jobs = find_jobs(sb)
        assets = load("asset-state.json").get("assets", [])
        for sc, _ in scene_prompts(sb):
            sid = str(sc["id"])
            j = jobs.get(sid)
            if not j:
                continue
            ent = state.setdefault(sid, {})
            ent.update(job=j["id"], status=j.get("status"), error=j.get("providerErrorCode"))
            if j.get("status") != "Completed" or ent.get("collected_job") == j["id"]:
                continue
            ast = asset_for(j, assets)
            if not ast:
                continue
            dst = os.path.join(clips, sc.get("clip") or f"scene_{int(sc['id']):02d}.mp4")
            shutil.copy2(ast["localPath"], dst)
            ent.update(collected_job=j["id"], file=dst, src=ast["localPath"], resolution=ast.get("resolution"))
            print(f"✓ Cảnh {sid} → {os.path.basename(dst)} ({ast.get('resolution', '?')})")
        json.dump(state, open(state_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        done, total = report(sb, jobs)
        got = sum(1 for sc, _ in scene_prompts(sb) if state.get(str(sc["id"]), {}).get("collected_job"))
        failed = [s for s, e in state.items() if e.get("status") == "Failed"]
        if got == total or time.time() >= deadline:
            break
        if failed and got + len(failed) == total:
            print("Còn cảnh thất bại:", ", ".join(failed))
            break
        time.sleep(15)
    print(f"Đã lấy {got}/{total} clip vào {clips}")


def cmd_images(a, sb, proj):
    """Ảnh AI: storyboard["image_jobs"] = [{"prompt": …, "dest": "ref/x.jpg"}] → chờ ảnh xong, chép về dest."""
    todo = [j for j in sb.get("image_jobs", []) if not (a.only and j["dest"] not in a.only)]
    deadline = time.time() + a.wait
    while True:
        jobs = [j for j in load("queue-state.json").get("jobs", []) if j.get("type") == "Image"]
        jobs.sort(key=lambda j: j.get("createdAt", ""), reverse=True)
        assets = load("asset-state.json").get("assets", [])
        left = 0
        for t in todo:
            if t.get("_done"):
                continue
            key = norm(t["prompt"])
            j = next((j for j in jobs if norm(j.get("payload", {}).get("prompt")) == key), None)
            st = j.get("status") if j else "CHƯA GỬI"
            if j and st == "Completed":
                ids = [x.get("url", "").rsplit("/", 1)[-1] for x in (j.get("result") or {}).get("assets", [])]
                ast = next((x for x in assets if x.get("type") == "image" and (x.get("jobId") == j["id"] or x.get("id") in ids)
                            and x.get("localPath") and os.path.isfile(x["localPath"])), None)
                if ast:
                    dst = os.path.join(proj, t["dest"])
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(ast["localPath"], dst)
                    t["_done"] = True
                    print(f"✓ {t['dest']} ← {os.path.basename(ast['localPath'])}")
                    continue
            if st == "Failed":
                print(f"✗ {t['dest']}: {j.get('providerErrorCode') or j.get('error', '')[:80]}")
                t["_done"] = True
                continue
            left += 1
        if not left or time.time() >= deadline:
            break
        time.sleep(10)
    print(f"Còn chờ {left} ảnh." if left else "Xong ảnh.")


ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["export", "status", "collect", "images"])
ap.add_argument("--only", nargs="*", help="images: chỉ lấy các dest này")
ap.add_argument("storyboard")
ap.add_argument("--clip", action="store_true")
ap.add_argument("--lines", action="store_true")
ap.add_argument("--refs", action="store_true")
ap.add_argument("--wait", type=int, default=0)
a = ap.parse_args()
sb = json.load(open(a.storyboard, encoding="utf-8"))
proj = os.path.dirname(os.path.abspath(a.storyboard))
{"export": cmd_export, "status": cmd_status, "collect": cmd_collect, "images": cmd_images}[a.cmd](a, sb, proj)
