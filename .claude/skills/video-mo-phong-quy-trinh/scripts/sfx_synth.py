"""Tạo bộ SFX + ambient + nhạc nền dịu bằng FFmpeg (miễn phí, chạy trên máy) → .claude/skills/video-mo-phong-quy-trinh/assets/sfx/*.wav

  python sfx_synth.py            # tạo các file còn thiếu
  python sfx_synth.py --force    # tạo lại tất cả

Để cho CapCut hậu kỳ đủ tiếng cho MỌI hành động (rain, wind, thunder, whoosh, sparkle, ding, chime, pop, hit, rise, heartbeat, crickets, birds, step, pad nhạc).
Âm thanh tổng hợp, đủ dùng cho video mẫu / lồng nền; muốn tiếng thật hơn thì thay file cùng tên bằng mẫu thật trong thư mục assets/sfx.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parents[1] / "assets" / "sfx"
OUT.mkdir(parents=True, exist_ok=True)


def tone(f, d, vol=0.5, fade_out=None):
    return f"sine=f={f}:d={d},volume={vol},afade=t=out:st={0 if fade_out is None else d - fade_out}:d={fade_out or d}"


SPEC = {
    # tên: (danh sách input lavfi, filter_complex hoặc -af, độ dài s)
    "swish": (["anoisesrc=d=0.9:c=pink:a=0.6"], "highpass=f=350,lowpass=f=4200,afade=t=in:d=0.3,afade=t=out:st=0.3:d=0.6,volume=1.6", .9),
    "whoosh": (["anoisesrc=d=1.4:c=pink:a=0.7"], "highpass=f=200,lowpass=f=2600,tremolo=f=3:d=0.4,afade=t=in:d=0.6,afade=t=out:st=0.6:d=0.8,volume=1.8", 1.4),
    "rain": (["anoisesrc=d=12:c=pink:a=0.5"], "highpass=f=1200,lowpass=f=9000,tremolo=f=11:d=0.35,volume=1.6,afade=t=in:d=0.5,afade=t=out:st=11.3:d=0.7", 12),
    "wind": (["anoisesrc=d=12:c=brown:a=0.9"], "lowpass=f=700,tremolo=f=0.35:d=0.7,volume=2.2,afade=t=in:d=1,afade=t=out:st=11:d=1", 12),
    "thunder": (["anoisesrc=d=3.5:c=brown:a=1.0"], "lowpass=f=260,afade=t=in:d=0.08,afade=t=out:st=0.2:d=3.3,volume=3.0", 3.5),
    "crickets": (["sine=f=4300:d=12"], "tremolo=f=28:d=1,tremolo=f=3.3:d=1,volume=0.5,afade=t=in:d=1,afade=t=out:st=11:d=1", 12),
    "birds": (["sine=f=3000:d=12"], "vibrato=f=11:d=0.9,tremolo=f=2.2:d=1,volume=0.35,lowpass=f=5000,afade=t=in:d=0.5,afade=t=out:st=11.3:d=0.7", 12),
    "pop": (["sine=f=780:d=0.14"], "afade=t=out:st=0.02:d=0.12,volume=0.9", .14),
    "ding": (["sine=f=1318:d=1.6", "sine=f=2637:d=1.6"], "[0]volume=0.6[a];[1]volume=0.25[b];[a][b]amix=inputs=2:normalize=0,afade=t=out:st=0.05:d=1.5", 1.6),
    "sparkle": (["sine=f=1568:d=0.9", "sine=f=2093:d=0.9", "sine=f=2637:d=0.9", "sine=f=3136:d=0.9"],
                "[0]volume=0.35,afade=t=out:st=0.1:d=0.8[a];[1]adelay=90|90,volume=0.3,afade=t=out:st=0.1:d=0.7[b];[2]adelay=180|180,volume=0.27,afade=t=out:st=0.1:d=0.6[c];[3]adelay=270|270,volume=0.22,afade=t=out:st=0.1:d=0.5[d];[a][b][c][d]amix=inputs=4:normalize=0", 1.0),
    "chime": (["sine=f=1047:d=2.2", "sine=f=1319:d=2.2", "sine=f=1568:d=2.2", "sine=f=2093:d=2.2"],
              "[0]volume=0.4,afade=t=out:st=0.1:d=2.0[a];[1]adelay=180|180,volume=0.35,afade=t=out:st=0.1:d=1.9[b];[2]adelay=360|360,volume=0.32,afade=t=out:st=0.1:d=1.8[c];[3]adelay=540|540,volume=0.3,afade=t=out:st=0.1:d=1.7[d];[a][b][c][d]amix=inputs=4:normalize=0", 2.4),
    "hit": (["anoisesrc=d=0.7:c=brown:a=1.0", "sine=f=55:d=0.7"], "[0]lowpass=f=300,afade=t=out:st=0.05:d=0.6,volume=2.0[a];[1]afade=t=out:st=0.05:d=0.6,volume=1.2[b];[a][b]amix=inputs=2:normalize=0", .7),
    "rise": (["aevalsrc=0.5*sin(2*PI*(180*t+260*t*t)):d=1.6:s=44100", "anoisesrc=d=1.6:c=pink:a=0.25"],
             "[0]afade=t=in:d=1.4,afade=t=out:st=1.4:d=0.2[a];[1]highpass=f=1500,afade=t=in:d=1.4,afade=t=out:st=1.4:d=0.2,volume=0.6[b];[a][b]amix=inputs=2:normalize=0,volume=1.2", 1.6),
    "heartbeat": (["sine=f=58:d=1.8"], "volume=0.9,tremolo=f=1.5:d=1,lowpass=f=140,afade=t=in:d=0.05,afade=t=out:st=1.5:d=0.3,volume=2.5", 1.8),
    "step": (["anoisesrc=d=0.18:c=brown:a=1"], "lowpass=f=500,afade=t=out:st=0.02:d=0.16,volume=2.0", .18),
    "slide": (["anoisesrc=d=1.2:c=pink:a=0.4"], "bandpass=f=900:w=500,tremolo=f=6:d=0.5,afade=t=in:d=0.3,afade=t=out:st=0.5:d=0.7,volume=1.4", 1.2),
    # nhạc nền dịu: pad hợp âm C-add9 + arpeggio nhẹ, ~80s (cắt theo độ dài video khi chèn)
    "pad_warm": (["sine=f=130.8:d=80", "sine=f=196:d=80", "sine=f=261.6:d=80", "sine=f=329.6:d=80", "sine=f=392:d=80"],
                 "[0]volume=0.35[a];[1]volume=0.25[b];[2]volume=0.22[c];[3]volume=0.15,tremolo=f=0.2:d=0.3[d];[4]volume=0.12,tremolo=f=0.15:d=0.4[e];[a][b][c][d][e]amix=inputs=5:normalize=0,lowpass=f=1800,tremolo=f=0.1:d=0.15,afade=t=in:d=3,afade=t=out:st=76:d=4", 80),
}


def main() -> None:
    force = "--force" in sys.argv
    for name, (ins, flt, dur) in SPEC.items():
        out = OUT / f"{name}.wav"
        if out.exists() and not force:
            continue
        cmd = ["ffmpeg", "-v", "error", "-y"]
        for i in ins:
            cmd += ["-f", "lavfi", "-i", i]
        if len(ins) == 1:
            cmd += ["-af", flt]
        else:
            cmd += ["-filter_complex", flt]
        cmd += ["-t", str(dur), "-ar", "44100", "-ac", "2", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if r.returncode:
            print(f"  ✗ {name}: {r.stderr.strip()[-200:]}")
            continue
        v = subprocess.run(["ffmpeg", "-i", str(out), "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True, errors="replace").stderr
        mx = next((l.split("max_volume:")[1].strip() for l in v.splitlines() if "max_volume" in l), "?")
        print(f"  ✓ {name}: {dur}s, đỉnh {mx}")
    print(f"OK: {len(list(OUT.glob('*.wav')))} file trong {OUT}")


if __name__ == "__main__":
    main()
