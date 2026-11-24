"""Đo từng bước của macro Studio Kịch Bản để tìm chỗ SỮNG/đứng chờ (chỉ nạp, KHÔNG bấm tạo, không tốn credit).

  python profile_macro.py projects/<slug>/storyboard.json
In bảng: thời điểm, thời gian mất, bước (chỉ các bước ≥0.6s) + tổng chờ cố định / expect / focus_app.
Quy tắc liền mạch: mọi bước trước khi bấm tạo phải < 2s trừ chờ giao diện thật sự cần; KHÔNG có bước kiểm nào chặn trước nút tạo.
"""
import argparse, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent.parent / "tao-video" / "scripts"))
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import tool_macro as M  # noqa: E402
import tool_story_macro as S  # noqa: E402

sb = Path(sys.argv[1]).resolve()
M.SHOTS = str(sb.parent / "_macro")
log, T0 = [], time.time()


def wrap(mod, name, label):
    f = getattr(mod, name)
    def g(*a, **k):
        t = time.time(); r = f(*a, **k); log.append((t - T0, time.time() - t, label, str(a)[:50], k.get("wait"))); return r
    setattr(mod, name, g)


for n in ("click", "key", "type_text", "focus_app", "shot"): wrap(M, n, n)
wrap(S, "expect", "expect")
ns = argparse.Namespace(storyboard=str(sb), provider="veo3", model="omni", dur=10, only_generate=False)
try:
    t = time.time(); S.build(ns); print(f"build tổng {time.time() - t:.1f}s")
except Exception as e:  # noqa: BLE001
    print("dừng:", e)
print("\n  t(s)  mất(s)  bước")
for t, d, l, a, w in log:
    if d >= 0.6 or l in ("expect", "focus_app"):
        print(f"{t:6.1f} {d:6.2f}  {l:10s} {a}  wait={w}")
fixed = sum(d for t, d, l, a, w in log if l in ("click", "key", "type_text"))
print(f"\nchờ cố định: {fixed:.1f}s · expect: {sum(d for t, d, l, a, w in log if l == 'expect'):.1f}s · focus_app: {sum(d for t, d, l, a, w in log if l == 'focus_app'):.1f}s")
