# DJF-Image effects

把一张（最好透明底的）主体图，用纯代码变成 **15 种 Illustrator 风格特效** 之一：
彩色半调、栅格化、铜版雕刻、点状化、晶格化、马赛克、染色玻璃、拼缀图、
绘图笔、图章、半调图案(直线)、径向模糊、图像描摹、高斯模糊+颗粒、玻璃。

全部用 **Pillow + NumPy** 实现，**不依赖任何 AI 生图模型**——
无水印、文字/边缘零漂移、参数可复现。输出默认保留透明通道，可直接做拼贴素材。

> English: A pure-Python (Pillow + NumPy) reimplementation of 15 classic Illustrator
> image effects. No AI image generation, no watermark, fully deterministic.
> Default output keeps the alpha channel for easy collage use.

---

## ✨ 特性

- **15 + 3 种效果**：15 种主效果外，另附高斯模糊、单色半调、像素化。
- **零 AI 依赖**：纯图像处理，离线可用，不产生积分消耗。
- **透明底友好**：默认保留 alpha，背景干净，适合拼贴/贴纸。
- **效果可叠加**：用 `--pipeline` 把多个效果串成流水线。
- **跨平台**：标准 Python 脚本，Windows / macOS / Linux 均可运行。
- **双模式**：既能在命令行直接跑，也能作为 [WorkBuddy](https://www.workbuddy.cn) 的 Skill 使用（见下文）。

---

## 📦 安装

需要 **Python 3.9+**。

```bash
pip install -r requirements.txt
```

`requirements.txt` 内容：

```
pillow>=9.0
numpy>=1.21
```

---

## 🚀 快速开始

```bash
# 彩色半调（默认 cell=8，可设 cell=0 启用自适应：最长边/135）
python scripts/apply_effects.py input.png output.png --effect halftone

# 中文效果名也能直接传
python scripts/apply_effects.py input.png output.png --effect 晶格化

# 马赛克，指定参数
python scripts/apply_effects.py input.png output.png --effect mosaic block=40 grout=0

# 效果叠加：先高斯模糊，再上彩色半调
python scripts/apply_effects.py input.png output.png --pipeline "gaussian:radius=3;halftone:cell=8"

# 查看全部效果与默认参数
python scripts/apply_effects.py --list
```

参数一律用 `键=值` 形式，例如 `cell=8`、`bg=transparent`、`threshold=0.6`。

大图默认自动缩到最长边 1400px（`--max-size 0` 可关闭限制）。

---

## 🎨 效果一览

| 名称 (key) | 中文 | 关键参数（默认值） | 说明 |
|---|---|---|---|
| `halftone` | 彩色半调 | `cell=8`(可设 `cell=0` 自适应), `gain=1.15` | RGB 三色网点罗纹排布，保留 alpha |
| `raster` | 栅格化 | `cell=10`, `ink=auto` | 对齐方格单色网点；`ink=auto` 取主体平均色 |
| `mezzotint` | 铜版雕刻 | `density=1.0` | 按明暗撒随机深/浅斑点，保留原色 |
| `pointillize` | 点状化 | `dot=9`, `density=1.6` | 随机圆点取主体色铺满轮廓 |
| `crystallize` | 晶格化 | `cell=18` | 全随机 Voronoi 多边形碎块 |
| `mosaic` | 马赛克 | `block=0`(自适应), `grout=2` | 方形色块+缝隙，缝隙只画在主体内 |
| `glass2` | 染色玻璃 | `cell=20`, `grout_w=2` | Voronoi 碎块 + 深色铅条缝 |
| `patchwork` | 拼缀图 | `block=30`, `shade=0.35` | 方块布片 + 折痕明暗 |
| `pen` | 绘图笔 | `period=7`, `angle=45`, `soft=1.4` | 斜向排线，暗处墨密、亮处留白 |
| `stamp` | 图章 | `threshold=0.5`, `rough=0.08`, `outline=2` | 高对比黑白剪影+噪点毛边 |
| `lines` | 半调图案(直线) | `period=8`, `angle=0` | 线宽随明暗变化的单向排线 |
| `radial` | 径向模糊 | `strength=0.25`, `steps=36` | 中心缩放叠加的 zoom blur |
| `trace` | 图像描摹 | `colors=6` | 中位切分量化为 N 色 |
| `blurgrain` | 高斯模糊+颗粒 | `radius=6`, `grain=16` | 高斯模糊再叠噪点颗粒 |
| `glass` | 玻璃 | `scale=14`, `strength=7` | 平滑噪声折射位移 + 边缘高光 |
| `gaussian` | 高斯模糊 *(附加)* | `radius=4` | RGB 全模糊，alpha 半量模糊 |
| `mono` | 单色半调 *(附加)* | `cell=8`, `angle=45` | 单色网点 |
| `pixelate` | 像素化 *(附加)* | `block=12` | 无缝隙纯马赛克块 |

效果名支持**中文别名直接传入**（如 `--effect 彩色半调`、`--effect 径向模糊`）。

透明底效果默认 `bg=transparent`；想还原「墨线+白纸」观感，给 `pen`/`lines`/`stamp`/`raster`/`mono` 传 `bg=white`。

示例输出见 [`assets/examples/`](assets/examples/)（原图 + 15 种效果 + 一图总览），中文对照说明见 [`docs/说明书.html`](docs/说明书.html)。

---

## 🖼 效果预览（在 GitHub 仓库页直接可见）

> 下面 15 张例图使用仓库相对路径，在 GitHub 仓库页面会**直接渲染**；原图为透明底 PNG（打电话的橘猫）。独立 HTML 说明书（`docs/说明书.html`）因 GitHub 不渲染其相对路径图片，建议在本地双击打开或启用 GitHub Pages 查看。

![](assets/examples/00-原图.png)

| 彩色半调 `halftone` | 栅格化 `raster` | 铜版雕刻 `mezzotint` |
|---|---|---|
| ![](assets/examples/01-彩色半调.png) | ![](assets/examples/02-栅格化.png) | ![](assets/examples/03-铜版雕刻.png) |

| 点状化 `pointillize` | 晶格化 `crystallize` | 马赛克 `mosaic` |
|---|---|---|
| ![](assets/examples/04-点状化.png) | ![](assets/examples/05-晶格化.png) | ![](assets/examples/06-马赛克.png) |

| 染色玻璃 `glass2` | 拼缀图 `patchwork` | 绘图笔 `pen` |
|---|---|---|
| ![](assets/examples/07-染色玻璃.png) | ![](assets/examples/08-拼缀图.png) | ![](assets/examples/09-绘图笔.png) |

| 图章 `stamp` | 半调图案(直线) `lines` | 径向模糊 `radial` |
|---|---|---|
| ![](assets/examples/10-图章.png) | ![](assets/examples/11-半调图案直线.png) | ![](assets/examples/12-径向模糊.png) |

| 图像描摹 `trace` | 高斯模糊+颗粒 `blurgrain` | 玻璃 `glass` |
|---|---|---|
| ![](assets/examples/13-图像描摹.png) | ![](assets/examples/14-高斯模糊颗粒.png) | ![](assets/examples/15-玻璃.png) |

> 另含附加效果 `gaussian` / `mono` / `pixelate`，详见 `python scripts/apply_effects.py --list`。

## 🤖 作为 WorkBuddy Skill 使用（可选）

本仓库本身就是一个合法的 WorkBuddy Skill。如果你用 WorkBuddy，把整个仓库放到：

```
~/.workbuddy/skills/djf-image-effects/
```

即可在对话里直接说「帮我把这个图片变成晶格化的」，Skill 会自动调用脚本出图。
详细说明见 [`SKILL.md`](SKILL.md)。

---

## 🌐 让任意 AI 助手使用（豆包 / Codex / Claude 等）

本仓库的特效引擎是**纯 Python 脚本**，不依赖 WorkBuddy。任何能跑命令/代码的 AI（Codex、Claude Code、豆包代码模式等）拿到仓库后都能调用。仓库根目录已附带多平台「说明书」，会被各家工具自动读取：

- `SKILL.md` —— WorkBuddy 专用（自然语言自动触发）
- `AGENTS.md` —— 通用 Agent 指令（Codex / Cursor / Gemini CLI 等遵循 agents.md 规范的工具自动读取）
- `CLAUDE.md` —— Claude Code 专用（自动读取）

**给你的 AI 一段可直接复制的提示词：**

> 这个仓库 `djf-image-effects` 是一个命令行图像特效工具。请用 `python scripts/apply_effects.py <图片路径> <输出.png> --effect <效果key>` 帮我处理这张图，效果用 <效果名>，参数用默认即可，处理完把结果给我。可用效果见 `python scripts/apply_effects.py --list`。

英文版说明见 [`README_EN.md`](README_EN.md)，英文说明书见 [`docs/manual-en.html`](docs/manual-en.html)。

---

## 📂 目录结构

```
djf-image-effects/
├── README.md                      本文件
├── LICENSE                        MIT
├── requirements.txt               pillow, numpy
├── SKILL.md                       WorkBuddy Skill 清单（可选）
├── scripts/
│   └── apply_effects.py           全部效果实现（唯一脚本）
├── assets/examples/               示例图（原图 + 15 效果 + 总览）
└── docs/
    └── 说明书.html                中文效果对照说明书
```

---

## 📄 许可证

[MIT](LICENSE) © 2026 DJF
