"""FRAME gate -- aspect ratio + blankable logo band

engine/postgate.py

Extracted VERBATIM from `engine/postgate.py` by `tools/build_modules.py`. Do not edit
this file: the function bodies below are copied byte-for-byte, and
`build_modules.py --check` fails if they drift from the source. To change the
gate, change it upstream and re-run the builder.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent

INK_V = 0.18


FRAME_TARGET = 2 / 3


FRAME_TOL = 0.06


LOGO_BAND = 0.16


LOGO_BLANK_V = 0.62


def load_grey(path: Path) -> np.ndarray:
    """Value channel in [0,1], as float64. Copies: asarray() is read-only."""
    with Image.open(path) as im:
        v = np.asarray(im.convert("L"), dtype=np.float64) / 255.0
    return v.copy()


def ink_frac(v: np.ndarray) -> float:
    return float((v < INK_V).mean())


def check_frame(path: Path) -> dict:
    """Aspect ratio plus logo-band blankability.

    Generate at the corpus ratio, then extend. Both 1:1 and 2:3 are legal
    states; anything else means the image came from somewhere else and the
    extend step cannot be trusted."""
    with Image.open(path) as im:
        w, h = im.size
    ratio = w / h
    off = {1.0: abs(ratio - 1.0), FRAME_TARGET: abs(ratio - FRAME_TARGET)}
    best = min(off, key=off.get)
    ok = off[best] <= FRAME_TOL

    band_top = int(h * (1 - LOGO_BAND))
    v = load_grey(path)
    band_ink = ink_frac(v[band_top:, :]) if band_top < h else float("nan")
    blankable = bool(band_top < h and band_ink <= LOGO_BLANK_V)

    return {
        "name": "frame",
        "pass": bool(ok and blankable),
        "w": w, "h": h, "ratio": round(ratio, 4),
        "closest": "square" if best == 1.0 else "2:3",
        "off_by": round(off[best], 4),
        "logo_band_ink": round(band_ink, 4),
        "logo_blankable": blankable,
        "detail": (f"{w}x{h} = {ratio:.3f}, closest "
                   f"{'1.000' if best == 1.0 else f'{FRAME_TARGET:.3f}'} "
                   f"(off by {off[best]:.3f}, tol {FRAME_TOL}); bottom "
                   f"{int(LOGO_BAND * 100)}% band ink {band_ink:.2f} "
                   f"(ceiling {LOGO_BLANK_V})"),
    }

# Moved here verbatim from postgate.py, which carried one shared list for all
# four gates. The FRAME gate's own honest limits, in its own words:
KNOWN_LIMITS = [
    "frame measures the aspect ratio of the file as delivered; it cannot say "
    "whether the buyer generated at that ratio or cropped into it, so a 1:1 "
    "crop of a 2:3 original passes identically.",
    "the logo-band blankability ceiling (ink <= 0.62 over the bottom 16%) is "
    "calibrated on this 48-image corpus. It is a ceiling for this corpus, not "
    "a law: a legitimately dense cover will be reported unblankable.",
]



def run(path) -> dict:
    path = Path(path)
    check = check_frame(path)
    return {"image": str(path), "pass": check["pass"], "checks": [check],
            "known_limits": KNOWN_LIMITS}


def _synthetic(tmp: Path) -> None:
    """Two controls. ink_frac counts DARK pixels (v < INK_V), so a blankable
    logo band is a LIGHT one. The first draft of this control drew the blank
    plate near-black and was itself rejected -- correctly -- which is the whole
    reason this function is asserted rather than assumed."""
    from PIL import ImageDraw as _D
    # cream plate: nothing dark anywhere -> ink_frac ~ 0 -> blankable
    Image.new("RGB", (900, 900), (235, 228, 210)).save(tmp / "square-blank.png")
    Image.new("RGB", (900, 1350), (235, 228, 210)).save(tmp / "two3-blank.png")
    # cream plate with a dense dark bottom band -> ink_frac ~ 1 -> NOT blankable
    busy = Image.new("RGB", (900, 1350), (235, 228, 210))
    d = _D.Draw(busy)
    for y in range(int(1350 * 0.84), 1350, 4):
        d.line([(0, y), (900, y)], fill=(15, 15, 20), width=3)
    busy.save(tmp / "two3-busy.png")


def selftest() -> int:
    """Prove the gate fires in both directions on synthetic images.

    A gate nobody has tried to break is an opinion, which is the whole reason
    validate_styleprint.py exists for the axes and --validate exists for the
    whole set. The cut halves need their own control or the split ships two
    untested files.
    """
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _synthetic(tmp)
        good = run(tmp / "two3-blank.png")
        square = run(tmp / "square-blank.png")
        bad = run(tmp / "two3-busy.png")
        if not good["pass"]:
            fails.append(f"legal 2:3 cream plate FAILED: {good['checks'][0]['detail']}")
        if not square["pass"]:
            fails.append(f"legal 1:1 cream plate FAILED: {square['checks'][0]['detail']}")
        if bad["pass"]:
            fails.append("dark logo band PASSED -- the gate is not firing")
        print(f"  legal 2:3 cream -> pass={good['pass']}  {good['checks'][0]['detail']}")
        print(f"  legal 1:1 cream -> pass={square['pass']}  {square['checks'][0]['detail']}")
        print(f"  banded 2:3      -> pass={bad['pass']}  (must be False)")
        print(f"  band ink         -> cream {good['checks'][0]['logo_band_ink']} "
              f"vs dark {bad['checks'][0]['logo_band_ink']} "
              f"(ceiling {LOGO_BLANK_V})")
    for f in fails:
        print(f"  FAIL {f}")
    print("PASS  frame: fires in both directions" if not fails
          else f"FAIL  frame: {len(fails)} control(s) wrong")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("image", nargs="?")
    ap.add_argument("--json", action="store_true", help="machine payload")
    ap.add_argument("--selftest", action="store_true",
                    help="run the synthetic controls and exit")
    ap.add_argument("--known-limits", action="store_true")
    a = ap.parse_args(argv)
    if a.known_limits:
        print(json.dumps(KNOWN_LIMITS, indent=1))
        return 0
    if a.selftest:
        return selftest()
    if not a.image:
        ap.print_help()
        return 2
    r = run(Path(a.image))
    print(json.dumps(r, indent=1) if a.json else
          f"{r['image']}  ->  {'PASS' if r['pass'] else 'REVIEW'}\n  " +
          "\n  ".join(f"[{'ok  ' if c['pass'] else 'WARN'}] {c['name']:11} "
                       f"{c['detail']}" for c in r["checks"]))
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
