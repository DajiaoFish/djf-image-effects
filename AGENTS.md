# DJF-Image effects — Agent Instructions

You are looking at the **DJF-Image effects** project: a pure-Python (Pillow + NumPy)
reimplementation of 15 classic Illustrator image effects. No AI image generation,
no watermark, fully deterministic and reproducible.

## When to use

When a user wants to turn a subject image (ideally a transparent-background PNG)
into one of these effects: color halftone, rasterize, mezzotint, pointillize,
crystallize, mosaic, stained glass, patchwork, graphic pen, stamp, halftone lines,
radial blur, image trace, gaussian blur + grain, glass — plus extras: gaussian,
monochrome halftone, pixelate.

The user may phrase it in Chinese or English, e.g.
"帮我把这个图片变成晶格化的" / "make this a color halftone" / "apply radial blur".

## How to invoke

```bash
python scripts/apply_effects.py <INPUT> <OUTPUT.png> --effect <key> [key=value ...]
```

- `<INPUT>` — the user's image path.
- `<OUTPUT.png>` — where to write (always PNG, keeps the alpha channel).
- `<key>` — one of the effect keys below. Chinese aliases are also accepted,
  e.g. `--effect 晶格化`.

### Effects

| key | name |
|---|---|
| `halftone` | Color Halftone |
| `raster` | Rasterize |
| `mezzotint` | Mezzotint |
| `pointillize` | Pointillize |
| `crystallize` | Crystallize |
| `mosaic` | Mosaic |
| `glass2` | Stained Glass |
| `patchwork` | Patchwork |
| `pen` | Graphic Pen |
| `stamp` | Stamp |
| `lines` | Halftone Lines |
| `radial` | Radial Blur |
| `trace` | Image Trace (N colors) |
| `blurgrain` | Gaussian Blur + Grain |
| `glass` | Glass |
| `gaussian` | Gaussian Blur (extra) |
| `mono` | Monochrome Halftone (extra) |
| `pixelate` | Pixelate (extra) |

### Compose effects

```bash
python scripts/apply_effects.py in.png out.png --pipeline "gaussian:radius=3;halftone:cell=8"
```

### Discover parameters

```bash
python scripts/apply_effects.py --list
```

## Rules

- **Do not ask for parameters.** Use the defaults, produce the image, then list
  the tunable params (`cell`, `strength`, `threshold`, `bg=white`) afterward.
- Output PNG and keep transparency. Do not alter the subject's actual content.
- If the input has a background (not transparent), mention it; `halftone` /
  `radial` / `trace` still work, but `mosaic` / `stamp` / `pen` / `lines` look
  best on transparent subjects.
- Requirements: `pip install -r requirements.txt` (pillow, numpy; Python 3.9+).
  Large images auto-scale to a longest side of 1400px (`--max-size 0` to disable).

## Examples

```bash
python scripts/apply_effects.py cat.png cat-halftone.png --effect halftone
python scripts/apply_effects.py cat.png cat-crystallize.png --effect crystallize
python scripts/apply_effects.py cat.png cat-mosaic.png --effect mosaic block=40 grout=0
```
