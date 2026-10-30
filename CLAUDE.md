# DJF-Image effects — Claude Code instructions

This is a CLI image-effects tool (pure Pillow + NumPy, no AI image generation).

To apply an effect to a user's image:

```bash
python scripts/apply_effects.py <INPUT> <OUTPUT.png> --effect <key> [key=value ...]
```

- Effects: `halftone`, `raster`, `mezzotint`, `pointillize`, `crystallize`,
  `mosaic`, `glass2`, `patchwork`, `pen`, `stamp`, `lines`, `radial`, `trace`,
  `blurgrain`, `glass`, `gaussian`, `mono`, `pixelate`.
  Chinese aliases also work, e.g. `--effect 晶格化`.
- Chain effects: `--pipeline "gaussian:radius=3;halftone:cell=8"`.
- List all effects with their parameters: `python scripts/apply_effects.py --list`.

Rules:
- Do **not** ask for parameters — use the defaults and deliver the PNG (it keeps
  the alpha channel). Then mention tunable params (`cell`, `strength`,
  `threshold`, `bg=white`).
- Requirements: `pip install -r requirements.txt` (pillow, numpy; Python 3.9+).

See `AGENTS.md` for the full effect table and conventions.
