# DJF-Image effects

Turn a subject image (ideally with a transparent background) into one of **15
Illustrator-style effects** — purely in code:

**Color Halftone, Rasterize, Mezzotint, Pointillize, Crystallize, Mosaic,
Stained Glass, Patchwork, Graphic Pen, Stamp, Halftone Lines, Radial Blur,
Image Trace (N colors), Gaussian Blur + Grain, Glass.**

Everything is implemented with **Pillow + NumPy** — **no AI image model
involved**. No watermark, zero text/edge drift, fully deterministic and
reproducible. Output keeps the alpha channel by default, so results drop
straight into collages and sticker sheets.

> 中文说明见 [`README.md`](README.md)。

---

## ✨ Features

- **15 + 3 effects**: the 15 main effects plus Gaussian blur, monochrome
  halftone, and pixelate.
- **Zero AI dependency**: pure image processing, runs fully offline, no
  generation credits burned.
- **Transparency-friendly**: alpha is preserved by default for clean
  backgrounds — great for collages / stickers.
- **Composable**: chain effects with `--pipeline`.
- **Cross-platform**: standard Python script, works on Windows / macOS / Linux.
- **Dual mode**: run it straight from the CLI, or use it as a
  [WorkBuddy](https://www.workbuddy.cn) Skill (see below).

---

## 📦 Installation

Requires **Python 3.9+**.

```bash
pip install -r requirements.txt
```

`requirements.txt`:

```
pillow>=9.0
numpy>=1.21
```

---

## 🚀 Quick start

```bash
# Color halftone (default cell=8; set cell=0 for auto: longest-side/135)
python scripts/apply_effects.py input.png output.png --effect halftone

# Chinese effect names also work directly
python scripts/apply_effects.py input.png output.png --effect 晶格化

# Mosaic with explicit params
python scripts/apply_effects.py input.png output.png --effect mosaic block=40 grout=0

# Compose: gaussian blur first, then color halftone
python scripts/apply_effects.py input.png output.png --pipeline "gaussian:radius=3;halftone:cell=8"

# List all effects and their default params
python scripts/apply_effects.py --list
```

Parameters are always `key=value`, e.g. `cell=8`, `bg=transparent`,
`threshold=0.6`.

Large images are auto-scaled to a longest side of 1400px by default
(`--max-size 0` disables the limit).

---

## 🎨 Effect reference

| Key | Name | Key params (default) | Notes |
|---|---|---|---|
| `halftone` | Color Halftone | `cell=8` (set `cell=0` for auto), `gain=1.15` | RGB tri-color dot rosettes, keeps alpha |
| `raster` | Rasterize | `cell=10`, `ink=auto` | aligned square single-color dots; `ink=auto` uses subject's average color |
| `mezzotint` | Mezzotint | `density=1.0` | random light/dark speckle by luminance, keeps original color |
| `pointillize` | Pointillize | `dot=9`, `density=1.6` | random subject-colored dots filling the silhouette |
| `crystallize` | Crystallize | `cell=18` | fully-random Voronoi polygon shards |
| `mosaic` | Mosaic | `block=0` (auto), `grout=2` | square tiles + grout; grout drawn only inside the subject |
| `glass2` | Stained Glass | `cell=20`, `grout_w=2` | Voronoi shards + dark lead seams |
| `patchwork` | Patchwork | `block=30`, `shade=0.35` | fabric squares + crease shading |
| `pen` | Graphic Pen | `period=7`, `angle=45`, `soft=1.4` | diagonal hatching, dark = dense ink, light = white space |
| `stamp` | Stamp | `threshold=0.5`, `rough=0.08`, `outline=2` | high-contrast B&W silhouette + noisy edge |
| `lines` | Halftone Lines | `period=8`, `angle=0` | one-directional lines whose width tracks luminance |
| `radial` | Radial Blur | `strength=0.25`, `steps=36` | center-zoom blur (zoom blur) via scaled overlay |
| `trace` | Image Trace | `colors=6` | median-cut quantization into N colors |
| `blurgrain` | Gaussian Blur + Grain | `radius=6`, `grain=16` | gaussian blur then film-grain noise |
| `glass` | Glass | `scale=14`, `strength=7` | smooth noise refraction displacement + edge highlights |
| `gaussian` | Gaussian Blur *(extra)* | `radius=4` | RGB fully blurred, alpha half-blurred |
| `mono` | Monochrome Halftone *(extra)* | `cell=8`, `angle=45` | single-color halftone |
| `pixelate` | Pixelate *(extra)* | `block=12` | gap-free pure mosaic blocks |

Effect names also accept **Chinese aliases directly** (e.g.
`--effect 彩色半调`, `--effect 径向模糊`).

Transparent-background effects default to `bg=transparent`; for the classic
"Illustrator ink-on-paper" look, pass `bg=white` to
`pen` / `lines` / `stamp` / `raster` / `mono`.

Example outputs live in [`assets/examples/`](assets/examples/) (source + 15
effects + one overview sheet). An English effect manual is at
[`docs/manual-en.html`](docs/manual-en.html); a Chinese comparison sheet is at
[`docs/说明书.html`](docs/说明书.html).

---

## 🖼 Effect Gallery (visible right on the GitHub repo page)

> The 15 example images below use repo-relative paths and render **directly on the
> GitHub repo page**. The source is a transparent-background PNG (an orange cat on the
> phone). The standalone HTML manual (`docs/manual-en.html`) does not render its
> relative images inside GitHub's file viewer — open it locally or enable GitHub Pages.

![](assets/examples/00-原图.png)

| Color Halftone `halftone` | Rasterize `raster` | Mezzotint `mezzotint` |
|---|---|---|
| ![](assets/examples/01-彩色半调.png) | ![](assets/examples/02-栅格化.png) | ![](assets/examples/03-铜版雕刻.png) |

| Pointillize `pointillize` | Crystallize `crystallize` | Mosaic `mosaic` |
|---|---|---|
| ![](assets/examples/04-点状化.png) | ![](assets/examples/05-晶格化.png) | ![](assets/examples/06-马赛克.png) |

| Stained Glass `glass2` | Patchwork `patchwork` | Graphic Pen `pen` |
|---|---|---|
| ![](assets/examples/07-染色玻璃.png) | ![](assets/examples/08-拼缀图.png) | ![](assets/examples/09-绘图笔.png) |

| Stamp `stamp` | Halftone Lines `lines` | Radial Blur `radial` |
|---|---|---|
| ![](assets/examples/10-图章.png) | ![](assets/examples/11-半调图案直线.png) | ![](assets/examples/12-径向模糊.png) |

| Image Trace `trace` | Gaussian Blur + Grain `blurgrain` | Glass `glass` |
|---|---|---|
| ![](assets/examples/13-图像描摹.png) | ![](assets/examples/14-高斯模糊颗粒.png) | ![](assets/examples/15-玻璃.png) |

> Extra effects `gaussian` / `mono` / `pixelate` are also available — see
> `python scripts/apply_effects.py --list`.

## 🤖 Using it as a WorkBuddy Skill (optional)

This repo is itself a valid WorkBuddy Skill. If you use WorkBuddy, drop the
whole repo at:

```
~/.workbuddy/skills/djf-image-effects/
```

Then in a chat just say "turn this image into a crystallize effect" and the
Skill calls the script for you. Full details in [`SKILL.md`](SKILL.md).

---

## 🌐 Use with any AI assistant (Doubao / Codex / Claude)

The effect engine is a **pure-Python script** with no WorkBuddy dependency. Any AI
that can run commands/code (Codex, Claude Code, Doubao's code mode, etc.) can call
it once it has the repo. The repo root already ships with multi-platform
instruction files that each tool auto-reads:

- `SKILL.md` — WorkBuddy only (natural-language auto-trigger)
- `AGENTS.md` — universal agent instructions (Codex / Cursor / Gemini CLI and other
  agents.md-compliant tools auto-read it)
- `CLAUDE.md` — Claude Code only (auto-read)

**A copy-paste prompt you can give your AI:**

> This repo `djf-image-effects` is a CLI image-effects tool. Run
> `python scripts/apply_effects.py <image path> <output.png> --effect <effect key>`
> to process this image with the <effect name>, using default parameters, and show
> me the result. See `python scripts/apply_effects.py --list` for available effects.

---

## 📂 Structure

```
djf-image-effects/
├── README.md                       Chinese docs
├── README_EN.md                    English docs (this file)
├── LICENSE                        MIT
├── requirements.txt               pillow, numpy
├── SKILL.md                       WorkBuddy Skill manifest (optional)
├── scripts/
│   └── apply_effects.py           all effects (the only script)
├── assets/examples/               sample images (source + 15 effects + overview)
└── docs/
    └── 说明书.html                 Chinese effect comparison sheet
```

---

## 📄 License

[MIT](LICENSE) © 2026 DJF
