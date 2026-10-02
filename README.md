# amph-frame-gate

**F5 FRAME** -- aspect ratio + blankable logo band

Aspect ratio plus logo-band blankability. A cover that is the wrong ratio came from somewhere else, and the extend step cannot be trusted.

## Run it

```bash
pip install -e .
python3 frame.py --selftest
```

## Where this came from

`frame.py` is extracted VERBATIM from `engine/postgate.py`
(sha8 `66296cf3`) by AST line range: the constants `INK_V, FRAME_TARGET,
FRAME_TOL, LOGO_BAND, LOGO_BLANK_V` and the functions `load_grey, ink_frac,
check_frame`. The bodies are byte-for-byte; only the header, the
limits list and the CLI are new.

Every file here is emitted by `amph-comic/tools/build_modules.py`, which copies
from `amph-public/engine/`. Nothing in this repo is hand-maintained. Regenerate
and verify with:

```bash
python3 tools/build_modules.py --check --out <this repo's parent>
```

## Known limits

This module ships its own limits rather than hiding them -- see `frame.py.py
--known-limits`, or `known-limits.json` in the F8 repo, which harvests all four.
