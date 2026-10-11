---
name: djf-image-effects
description: DJF-Image effects · 主体图特效变换技能。用户发来一张（最好透明底的）人物/动物主体图片，并说一句"帮我把这个图片变成 XX"，即可用纯图像处理代码（Pillow+numpy；不消耗 AI 生图积分、无水印、确定性可复现）把主体变成 15 种 Illustrator 风格效果之一：彩色半调、栅格化、铜版雕刻、点状化、晶格化、马赛克、染色玻璃、拼缀图、绘图笔、图章、半调图案(直线)、径向模糊、图像描摹(N色)、高斯模糊+颗粒、玻璃；另附加高斯模糊、单色半调、像素化，支持效果叠加。当用户要求把图片变成某种滤镜/特效效果、提到 djf-image-effects 或 DJF-Image effects 时使用。
agent_created: true
---

# DJF-Image effects · 主体图特效变换

对照 Illustrator「图像效果」15 种效果的纯代码实现。**典型用法**：用户丢来一张主体图 + 一句效果名，直接出图——不消耗 AI 生图积分、不产生水印、文字/边缘零漂移。

用户那句话通常很短，识别效果名即可开工，**不要追问参数**：

| 用户可能这么说 | 识别为 | 执行 |
|---|---|---|
| "帮我把这个图片变成栅格化的" | raster | `--effect raster` |
| "来张彩色半调" / "做成半调网点" | halftone | `--effect halftone` |
| "变成晶格化/染色玻璃/马赛克那样" | crystallize / glass2 / mosaic | 对应 --effect |
| "加点径向模糊" / "高斯模糊+颗粒" | radial / blurgrain | 对应 --effect |
| "做成黑白排线的" | lines 或 pen | 按参照图风格选 |

## 使用流程

1. **取输入**：主体图（透明底最佳）+ 效果名。效果名中英文、别名都能直接用（走 `ALIASES` 表）。
2. **非透明底**：先告知用户并询问是否抠图（可调用 buddy-image-processing 的抠图能力）；halftone / radial / trace 等对非透明底也能直接跑。
3. **执行**（Python 用隔离 venv）：

   ```bash
   C:/Users/NatalieRu/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
     "C:/Users/NatalieRu/.workbuddy/skills/djf-image-effects/scripts/apply_effects.py" \
     "<输入图>" "<输出图.png>" --effect <效果名> [k=v ...]
   ```

   - 组合效果：`--pipeline "gaussian:radius=3;halftone:cell=8"`（从左到右依次叠加）
   - 查全部效果与参数：`--list`
   - 参数一律 `k=v` 形式，如 `cell=8`、`bg=transparent`
4. **目检**：用 Read 查看输出——网点/碎块/排线清晰，主体轮廓完整。不合格先调参数重跑再交付。
5. **交付**：给出 PNG，附一句关键可调参数（网点 cell / 碎块 cell / 模糊强度 / 网格 block），邀请微调。

用户没说参数就用默认值先出一版，让用户看着实物调，比追问参数快。

## 效果总览

`assets/examples/overview-15-effects.png` 是 15 种效果一图总览（含中文标签），首次使用先看它对齐预期。

| 效果名 | 中文 | 关键参数（默认值） | 说明 |
|---|---|---|---|
| halftone | 彩色半调 | cell=8(可设 cell=0 自适应:最长边/135), gain=1.15 | RGB 三色网点罗纹排布，保留 alpha；cell=0 启用自适应 |
| raster | 栅格化 | cell=10, ink=auto, bg=transparent | 对齐方格单色网点；ink=auto 取主体平均色加深，也可给 #hex |
| mezzotint | 铜版雕刻 | density=1.0 | 按明暗撒随机深/浅斑点，保留原色 |
| pointillize | 点状化 | dot=9, density=1.6 | 随机圆点取主体色铺满轮廓 |
| crystallize | 晶格化 | cell=18 | 全随机种子 Voronoi 多边形碎块，每块取种子点颜色 |
| mosaic | 马赛克 | block=0(自适应:最长边/34,最小10), grout=2 | 方形色块+缝隙；缝隙只画在主体内部，默认白色 |
| glass2 | 染色玻璃 | cell=20, grout_w=2 | Voronoi 碎块 + 深色铅条缝（#191919） |
| patchwork | 拼缀图 | block=30, shade=0.35 | 方块布片 + 对角折痕明暗 + 接缝 |
| pen | 绘图笔 | period=7, angle=45, bg=transparent, soft=1.4 | 斜向排线，暗处墨密、亮处留白 |
| stamp | 图章 | threshold=0.5, rough=0.08, outline=2 | 高对比黑白剪影+噪点毛边；outline>0 沿主体轮廓描墨线 |
| lines | 半调图案(直线) | period=8, angle=0, bg=transparent | 线宽随明暗变化的单向排线 |
| radial | 径向模糊 | strength=0.25, steps=36 | 中心缩放叠加的 zoom blur；预乘 alpha 累加，避免透明区灰边 |
| trace | 图像描摹(N色) | colors=6 | 中位切分量化为 N 色，保留 alpha |
| blurgrain | 高斯模糊+颗粒 | radius=6, grain=16 | 先高斯模糊再叠噪点颗粒 |
| glass | 玻璃 | scale=14, strength=7 | 平滑噪声折射位移 + 轻微边缘高光 |
| gaussian | 高斯模糊(附加) | radius=4 | RGB 全模糊，alpha 半量模糊保轮廓 |
| mono | 单色半调(附加) | cell=8, angle=45, bg=white | 单色网点 |
| pixelate | 像素化(附加) | block=12, gap=0 | 无缝隙纯马赛克块 |

默认**全部保留透明底**（`bg=transparent`），方便直接做拼贴素材；要还原 Illustrator 参考图那种「墨线+白纸」观感，给 pen / lines / stamp / raster / mono 传 `bg=white`。

## 硬性规则

- 输出一律 PNG，保留透明通道；**禁止改动主体内容本身**（不磨皮、不重绘、不变形）。
- 用户只说效果名 → 用默认参数直接出图，交付后再列可调参数。
- 大图自动缩到最长边 1400px（`--max-size` 可调，0=不限制）。
- 效果名支持中文别名直接传入（"彩色半调""晶格化""径向模糊"等）。
- 目检不通过（网点糊成一片 / 碎块过大 / 轮廓丢失）先调参数重跑，不得直接交付。

## 资源文件

```
djf-image-effects/
├── SKILL.md                        本文件
├── scripts/apply_effects.py        全部效果的实现（唯一脚本，18 个效果）
└── assets/examples/
    ├── overview-15-effects.png     15 效果一图总览（含中文标签）
    ├── sample-halftone.png         彩色半调样例
    ├── sample-crystallize.png      晶格化样例
    ├── sample-stained-glass.png    染色玻璃样例
    └── sample-pen.png              绘图笔样例
```

依赖：Pillow、numpy（隔离 venv `C:/Users/NatalieRu/.workbuddy/binaries/python/envs/default` 内已装好）。

## 实现备注（改脚本前先读）

- Voronoi 系（crystallize / glass2）：种子点**完全随机撒点** + 分块最近邻（`_voronoi_map`）。早期「网格抖动」版本会呈现明显方格网感，已被否决，勿改回。
- 半调/网点系：`_dot_layer` 在超采样画布（ss=2）上画点再降采样，保证点边缘平滑；`dark` 图先做 `GaussianBlur(cell*0.35)` 防止网点抖动。
- `glass` 的位移场用**两步 BICUBIC** 上采样（`_make_field`）；单步 BILINEAR 会在格子边界产生折痕，形成脏噪感。
- `mosaic` 缝隙、`glass2` 铅条都必须**限制在主体 alpha 内**，且 alpha 与 RGB 要**同步恢复原值**（mosaic 先整体刷缝色再还原，未覆盖处必须还原 `rgb0`，否则透明区残留白色 RGB，预览器和部分渲染器会出现满屏网格/光晕）。
- `pointillize` 只画采样点 alpha>40 的点，避免在空白区撒点。
- `pen` 的 `soft` 是**最容易设错**的参数：它把 `(1-lum)` 线性放大成墨覆盖度，`soft` 过大（如 3.2）会把中间调全部顶到 1，整只主体糊成一块均匀密线、浅色区完全没层次。实测安全值 `soft≈1.4` + 0.10 死区、线覆盖率约 50%（`wave>0`）。改这个函数前先用一张真实照片验证明暗层次，别只看纯色块测试图。
- `radial` 必须用**预乘 alpha** 累加（先 `rgb*=a`，累加后除以 a），否则透明区的 RGB 会渗进主体边缘形成灰边/白晕；steps 低于 ~30 会出现同心环带，默认 36。
- `stamp` 单靠亮度阈值做会「糊成一团黑」：透明底主体上浅色区域（白毛、白衣）全被滤掉，只剩暗部成块，形状不可辨。因此默认开 `outline=2`，用主体二值 alpha 做 MinFilter 腐蚀取边、再 `lighter` 合成，保证外形始终可读；判定用的 alpha 也换成二值化版本，边缘更硬朗、更像印章。
- 网点类参数（`halftone.cell`、`mosaic.block`）**都要随图分辨率自适应**，固定像素值在不同尺寸图上观感差异极大。halftone 用 `cell<=0` → 最长边/135；mosaic 用 `block<=0` → 最长边/34。给大图（>2000px）出图前务必确认这一点，否则会密成噪点。
