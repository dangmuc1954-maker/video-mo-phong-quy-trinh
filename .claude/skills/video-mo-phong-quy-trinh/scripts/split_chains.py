"""Chia storyboard thành các chuỗi cảnh (theo trường "chain") để tạo SONG SONG trong Studio Kịch Bản.
  python split_chains.py projects/<slug>/storyboard.json   →  storyboard_A.json, storyboard_B.json (mỗi file chỉ gồm cảnh của chuỗi đó)
Mỗi chuỗi là một dự án kịch bản riêng trong tool; cảnh đầu mỗi chuỗi tự gắn ảnh tham chiếu (reference_images)."""
import json
import sys
from pathlib import Path

sbp = Path(sys.argv[1]).resolve()
sb = json.loads(sbp.read_text(encoding="utf-8"))
chains = {}
for s in sb["scenes"]:
    chains.setdefault(s.get("chain", "A"), []).append(s)
for k, scenes in chains.items():
    d = dict(sb)
    d["scenes"] = scenes
    d["title"] = f"{sb.get('title', 'video')} - chuoi {k}"
    (sbp.parent / f"storyboard_{k}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"chuỗi {k}: cảnh {[s['id'] for s in scenes]}")
