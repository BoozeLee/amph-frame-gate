#!/usr/bin/env python3
"""Self-check for amph-frame-gate -- runs from a fresh clone, with no corpus.

frame is calibrated on real plates, so a fresh clone has no input it can PASS on. The control here is the FAIL direction on synthetic art plus a parseable payload and a readable limits record. The PASS direction needs the corpus and is deliberately not asserted.

Exits 0 only if every assertion below holds.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from PIL import Image, ImageDraw


def run(tmp: Path) -> int:
    blank = tmp / "blank.jpg"
    framed = tmp / "framed.jpg"
    Image.new("RGB", (600, 600), (12, 12, 16)).save(blank, "JPEG", quality=92)
    im = Image.new("RGB", (600, 600), (12, 12, 16))
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, 560, 560], outline=(240, 240, 240), width=12)
    im.save(framed, "JPEG", quality=92)

    for p in (blank, framed):
        r = subprocess.run([sys.executable, "frame.py", str(p), "--json"],
                           cwd=HERE, capture_output=True, text=True)
        try:
            doc = json.loads(r.stdout)
        except json.JSONDecodeError:
            print(f"FAIL no parseable payload on {p.name} "
                  f"(rc={r.returncode}):", (r.stdout + r.stderr).strip()[-300:])
            return 1
        if "pass" not in doc:
            print(f"FAIL payload on {p.name} carries no pass field: "
                  f"{sorted(doc)}")
            return 1
        names = [c.get("name") for c in doc.get("checks", [])]
        if "frame" not in names:
            print(f"FAIL payload on {p.name} has no frame check: {names}")
            return 1

    # Measured FAIL direction: synthetic art is not a frame.
    r2 = subprocess.run([sys.executable, "frame.py", str(blank), "--json"],
                        cwd=HERE, capture_output=True, text=True)
    if json.loads(r2.stdout).get("pass") is not False:
        print("FAIL a blank canvas passed the frame gate; the gate is "
              "calibrated on real art and must not accept anything")
        return 1

    r3 = subprocess.run([sys.executable, "frame.py", "--known-limits"],
                        cwd=HERE, capture_output=True, text=True)
    if r3.returncode or not r3.stdout.strip():
        print("FAIL --known-limits produced nothing:", (r3.stdout + r3.stderr).strip()[-300:])
        return 1

    print("PASS  frame: payload parses with a frame check; blank FAILS; "
          "limits readable")
    print("NOTE  frame's PASS direction needs real plates and is NOT asserted "
          "here -- no synthetic substitute was found that it accepts")
    return 0


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="amph-frame-gate-selftest-"))
    try:
        return run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
