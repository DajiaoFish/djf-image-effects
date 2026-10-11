#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""subject-effects · 主体图特效变换工具（对照 Illustrator 效果 15 种）

用法:
  python apply_effects.py INPUT OUTPUT --effect halftone cell=8
  python apply_effects.py INPUT OUTPUT --pipeline "gaussian:radius=3;halftone:cell=8"
  python apply_effects.py INPUT OUTPUT --list        查看全部效果

全部效果（中文别名可直接当效果名用）:
  halftone      彩色半调     raster        栅格化
  mezzotint     铜版雕刻     pointillize   点状化
  crystallize   晶格化       mosaic        马赛克
  glass2        染色玻璃     patchwork     拼缀图
  pen           绘图笔       stamp         图章
  lines         半调图案(直线)
  radial        径向模糊     trace         图像描摹(N色)
  blurgrain     高斯模糊+颗粒 glass        玻璃
  gaussian      高斯模糊(附加) mono        单色半调(附加)
"""
import argparse
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

# ---------------------------------------------------------------- utilities

def load_rgba(path):
    return Image.open(path).convert("RGBA")


def clamp_max_size(img, max_size):
    if max_size and max(img.size) > max_size:
        s = max_size / max(img.size)
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    return img


def _lum(img):
    """亮度 0..1 的 float 数组"""
    return np.asarray(img.convert("L"), dtype=np.float32) / 255.0


def _rng(seed):
    return np.random.default_rng(seed)


def _bg_color(bg):
    """'transparent' | 'white' | '#RRGGBB' -> (r,g,b,a)"""
    if bg == "transparent":
        return (255, 255, 255, 0)
    if bg == "white":
        return (255, 255, 255, 255)
    return tuple(int(bg[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def _hex_rgb(v, default=(17, 17, 17)):
    if not v or v == "auto":
        return tuple(default)
    return tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))


def _auto_ink(img, factor=0.55):
    """从主体平均色派生一个深色墨色"""
    a = np.asarray(img)
    mask = a[..., 3] > 128
    if not mask.any():
        return (17, 17, 17)
    mean = a[mask][:, :3].mean(axis=0)
    return tuple(int(c * factor) for c in mean)


# ---------------------------------------------------- halftone primitives

def _dot_layer(size, dark, cell, angle, gain, ss):
    """旋转网格黑点层（白底 L 模式）。dark: 0..1，越大点越大。"""
    W, H = size
    Ws, Hs = W * ss, H * ss
    cells = max(2, int(round(cell * ss)))
    layer = Image.new("L", (Ws, Hs), 255)
    d = ImageDraw.Draw(layer)
    dark_img = Image.fromarray((np.clip(dark, 0, 1) * 255).astype(np.uint8))
    if dark_img.size != (Ws, Hs):
        dark_img = dark_img.resize((Ws, Hs), Image.BILINEAR)
    px = dark_img.load()
    dw, dh = dark_img.size
    th = math.radians(angle)
    c, s = math.cos(th), math.sin(th)
    R = math.hypot(Ws, Hs) / 2 + cells * 2
    n = int(R / cells) + 1
    hw, hh = Ws / 2, Hs / 2
    for i in range(-n, n + 1):
        x0 = i * cells
        for j in range(-n, n + 1):
            y0 = j * cells
            x = hw + x0 * c - y0 * s
            y = hh + x0 * s + y0 * c
            if x < -cells or x > Ws + cells or y < -cells or y > Hs + cells:
                continue
            xi = 0 if x < 0 else (dw - 1 if x >= dw else int(x))
            yi = 0 if y < 0 else (dh - 1 if y >= dh else int(y))
            v = px[xi, yi] / 255.0
            r = (v ** 0.6) * cells * 0.62 * gain
            if r >= 0.7:
                d.ellipse([x - r, y - r, x + r, y + r], fill=0)
    if ss > 1:
        layer = layer.resize((W, H), Image.LANCZOS)
    return layer


# ---------------------------------------------------------------- 1 彩色半调

def fx_halftone(img, cell=0, angle_r=15, angle_g=75, angle_b=0, gain=1.15, ss=2):
    """彩色半调：R/G/B 三通道各自网点 + 传统网角 15/75/0。

    cell<=0 时按最长边自适应（最长边/135），保证不同分辨率图片的网点
    **视觉密度一致**——否则 3000px 大图用 cell=8 会密成噪点，
    小图用 cell=8 又会糊成色块。
    """
    if cell <= 0:
        cell = max(3, int(round(max(img.size) / 135)))
    rgb = img.convert("RGB")
    channels = []
    for ch, ang in zip(rgb.split(), (angle_r, angle_g, angle_b)):
        dark = 1.0 - np.asarray(ch.convert("L"), dtype=np.float32) / 255.0
        dark = np.asarray(Image.fromarray((dark * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(max(1.0, cell * 0.35))), dtype=np.float32) / 255.0
        channels.append(_dot_layer(img.size, dark, cell, ang, gain, ss))
    return Image.merge("RGBA", (*channels, img.getchannel("A")))


# ---------------------------------------------------------------- 2 栅格化

def fx_raster(img, cell=10, ink="auto", gain=1.25, bg="transparent"):
    """栅格化：对齐方格网点（无旋转），单色墨点。ink=auto 取主体平均色加深。"""
    ink_rgb = _auto_ink(img) if ink == "auto" else _hex_rgb(ink)
    dark = 1.0 - np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    dark = np.asarray(Image.fromarray((dark * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(max(1.0, cell * 0.3))), dtype=np.float32) / 255.0
    layer = _dot_layer(img.size, dark, cell, 0, gain, 2)  # 白底黑点
    cov = ImageOps.invert(layer)  # 墨量
    alpha = ImageChops.multiply(cov, img.getchannel("A"))
    base = Image.new("RGBA", img.size, _bg_color(bg))
    ink_layer = Image.new("RGBA", img.size, ink_rgb + (255,))
    return Image.composite(ink_layer, base, alpha)


# ---------------------------------------------------------------- 3 铜版雕刻

def fx_mezzotint(img, density=1.0, dark_gain=0.55, bright_gain=0.25, seed=7):
    """铜版雕刻：按明暗撒随机深/浅色斑点。"""
    a = np.asarray(img, dtype=np.float32)
    lum = a[..., :3].mean(axis=2) / 255.0
    alpha = a[..., 3:4]
    rng = _rng(seed)
    noise = rng.random(lum.shape, dtype=np.float32)
    h, w = lum.shape
    rand_dark = (0.35 + rng.random((h, w), dtype=np.float32) * 0.35)
    rand_bright = (1.3 + rng.random((h, w), dtype=np.float32) * 0.6)
    p_dark = np.clip((1.0 - lum) * density * 0.9, 0, 1)
    p_bright = np.clip((lum - 0.55) * density * 0.5, 0, 1)
    rgb = a[..., :3] / 255.0
    is_dark = (noise < p_dark) & (alpha[..., 0] > 0)
    is_bright = (noise > 1.0 - p_bright) & (alpha[..., 0] > 0)
    rgb = rgb * rand_dark[..., None] * is_dark[..., None] + rgb * (1 - is_dark[..., None])
    rgb = np.clip(rgb * rand_bright[..., None] * is_bright[..., None] + rgb * (1 - is_bright[..., None]), 0, 1)
    out = np.concatenate([rgb * 255.0, alpha], axis=2).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


# ---------------------------------------------------------------- 4 点状化

def fx_pointillize(img, dot=9, density=1.6, bg="transparent", seed=11):
    """点状化：随机圆点取主体颜色，点满主体轮廓。"""
    W, H = img.size
    arr = np.asarray(img)
    base = Image.new("RGBA", (W, H), _bg_color(bg))
    d = ImageDraw.Draw(base)
    rng = _rng(seed)
    n = int(W * H / (dot * dot) * density)
    for _ in range(n):
        x = rng.random() * W
        y = rng.random() * H
        xi, yi = int(x) % W, int(y) % H
        r0, g0, b0, a0 = arr[yi, xi]
        if a0 < 40:
            continue
        rad = dot * (0.45 + rng.random() * 0.45)
        d.ellipse([x - rad, y - rad, x + rad, y + rad],
                  fill=(int(r0), int(g0), int(b0), int(a0)))
    return base


# ------------------------------------------------- 晶格化 / 染色玻璃 共用

def _voronoi_map(W, H, cell, jitter, rng):
    """返回 label 图（每个像素最近随机种子点的编号）与种子点坐标。
    种子完全随机撒点（非网格抖动），保证有机的多边形碎块感。"""
    n = max(4, int(round(W * H / (cell * cell) * 1.15)))
    sx = (rng.random(n) * W).astype(np.float32)
    sy = (rng.random(n) * H).astype(np.float32)
    xs = np.arange(W, dtype=np.float32) + 0.5
    ys = np.arange(H, dtype=np.float32) + 0.5
    label = np.empty((H, W), dtype=np.int64)
    rows = max(1, int(24_000_000 // (W * n)))  # 控制单块内存 ~100MB
    for y0 in range(0, H, rows):
        y1 = min(H, y0 + rows)
        d2 = ((xs[None, None, :] - sx[None, :, None]) ** 2 +
              (ys[y0:y1, None, None] - sy[None, :, None]) ** 2)
        label[y0:y1] = np.argmin(d2, axis=1)
    centers = np.stack([sx, sy], axis=1)
    return label, centers


def fx_crystallize(img, cell=18, jitter=0.9, seed=3):
    """晶格化：Voronoi 多边形填充，每格取种子点颜色。"""
    W, H = img.size
    arr = np.asarray(img)
    rng = _rng(seed)
    label, centers = _voronoi_map(W, H, cell, jitter, rng)
    cxi = np.clip(centers[:, 0].astype(int), 0, W - 1)
    cyi = np.clip(centers[:, 1].astype(int), 0, H - 1)
    cell_colors = arr[cyi, cxi]  # (N,4)
    out = cell_colors[label]
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def fx_stained_glass(img, cell=20, jitter=0.9, grout=(25, 25, 25), grout_w=2, seed=5):
    """染色玻璃：Voronoi 格 + 深色铅条缝。"""
    W, H = img.size
    arr = np.asarray(img)
    rng = _rng(seed)
    label, centers = _voronoi_map(W, H, cell, jitter, rng)
    cxi = np.clip(centers[:, 0].astype(int), 0, W - 1)
    cyi = np.clip(centers[:, 1].astype(int), 0, H - 1)
    out = cell_colors = arr[cyi, cxi][label].astype(np.float32)
    cell_alpha = cell_colors[..., 3] if cell_colors.ndim == 2 else cell_colors[..., 3]
    # 铅条：label 与右/下邻居不同处涂缝
    edge = np.zeros((H, W), dtype=bool)
    edge[:, :-1] |= label[:, 1:] != label[:, :-1]
    edge[:-1, :] |= label[1:, :] != label[:-1, :]
    for k in range(1, grout_w):
        e = np.zeros_like(edge)
        e[:, k:] |= edge[:, :-k]
        e[k:, :] |= edge[:-k, :]
        e[:, :-k] |= edge[:, k:]
        e[:-k, :] |= edge[k:, :]
        edge |= e
    out[..., :3] = np.where(edge[..., None], np.array(grout, dtype=np.float32), out[..., :3])
    # 铅条只画在主体覆盖处；透明格保持透明
    base_a = np.asarray(arr)[cyi, cxi][label][..., 3].astype(np.float32)
    out[..., 3] = np.where(edge & (base_a > 0), 255.0, base_a)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- 6 马赛克

def fx_mosaic(img, block=0, grout=2, grout_color="white"):
    """马赛克：方形色块 + 缝隙（grout=0 无缝）。缝隙只画在主体内部。
    block=0 时自适应：最长边/34（最小 10），贴近参考图的块大小。"""
    W, H = img.size
    if not block:
        block = max(10, round(max(W, H) / 34))
    bw, bh = max(1, W // block), max(1, H // block)
    small = img.resize((bw, bh), Image.BOX)
    out = small.resize((W, H), Image.NEAREST)
    if grout and grout > 0:
        gc = _bg_color(grout_color)
        a = np.asarray(out).copy()
        alpha0 = a[..., 3].copy()
        rgb0 = a[..., :3].copy()
        g = grout
        for x in range(0, W, block):
            a[:, x:x + g] = gc if x + g <= W else a[:, x:x + g]
        for y in range(0, H, block):
            a[y:y + g] = gc if y + g <= H else a[y:y + g]
        # 缝隙只保留在主体覆盖区域
        tile_covered = np.asarray(small)[..., 3] > 0  # (bh,bw) 每块是否覆盖主体
        covered = np.repeat(np.repeat(tile_covered, block, 0), block, 1)
        covered = np.pad(covered, ((0, H - covered.shape[0]), (0, W - covered.shape[1])), mode="edge")
        grout_mask = np.zeros((H, W), dtype=bool)
        for x in range(0, W, block):
            grout_mask[:, x:x + g] = True
        for y in range(0, H, block):
            grout_mask[y:y + g] = True
        visible = grout_mask & covered
        a[..., 3] = np.where(visible, 255, alpha0)
        for c in range(3):
            a[..., c] = np.where(visible, gc[c], rgb0[..., c])
        out = Image.fromarray(a, "RGBA")
    return out


# ---------------------------------------------------------------- 7 拼缀图

def fx_patchwork(img, block=30, seam=2, shade=0.35):
    """拼缀图：方块布片 + 对角折痕明暗 + 接缝。"""
    W, H = img.size
    arr = np.asarray(img, dtype=np.float32)
    bw, bh = max(2, W // block), max(2, H // block)
    small = img.resize((bw, bh), Image.BOX)
    cells = np.asarray(small, dtype=np.float32)  # (bh,bw,4)
    # 单块明暗模板：左上亮右下暗 + 对角折痕
    yy, xx = np.mgrid[0:block, 0:block]
    t = (xx + yy) / (2 * (block - 1))
    tri = (xx > yy).astype(np.float32)  # 对角折痕：右上三角略亮
    tmpl = 1.0 + shade * (0.5 - t) * 2 * 0.5 + tri * shade * 0.18 - (1 - tri) * shade * 0.10
    tmpl = tmpl[..., None]
    ny, nx = H // block + 1, W // block + 1
    tiled = np.tile(tmpl, (ny, nx, 1))[:H, :W]
    up = np.asarray(Image.fromarray(cells.astype(np.uint8)).resize((W, H), Image.NEAREST),
                    dtype=np.float32)
    rgb = np.clip(up[..., :3] * tiled, 0, 255)
    out = np.concatenate([rgb, up[..., 3:4]], axis=2)
    # 接缝
    s = seam
    if s > 0:
        for x in range(0, W, block):
            out[:, x:x + s, :3] *= 0.45
        for y in range(0, H, block):
            out[y:y + s, :3] *= 0.45
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- 8 绘图笔

def fx_pen(img, period=7, angle=45, ink=(25, 25, 25), bg="transparent", soft=1.4):
    """绘图笔：斜向排线，暗处线密、亮处留白。

    darkness 必须落在 0..1 的宽区间：`soft` 过大会把中间调全部拉满，
    整只主体糊成一块均匀密线，浅色区（白毛/白衣）看不出层次。
    实测安全值 soft≈1.4 + 0.10 死区。
    """
    W, H = img.size
    lum = _lum(img)
    darkness = np.clip((1.0 - lum - 0.10) * soft, 0, 1) ** 1.05
    yy, xx = np.mgrid[0:H, 0:W]
    th = math.radians(angle)
    wave = np.sin((xx * math.cos(th) + yy * math.sin(th)) * 2 * math.pi / period)
    stroke = wave > 0.0  # 约 50% 覆盖，线宽≈空隙
    cov = (stroke * darkness * 255).astype(np.uint8)
    alpha = ImageChops.multiply(Image.fromarray(cov, "L"), img.getchannel("A"))
    base = Image.new("RGBA", (W, H), _bg_color(bg))
    ink_layer = Image.new("RGBA", (W, H), tuple(ink) + (255,))
    return Image.composite(ink_layer, base, alpha)


# ---------------------------------------------------------------- 9 图章

def fx_stamp(img, threshold=0.5, rough=0.08, ink=(20, 20, 20), bg="white", outline=2):
    """图章：高对比黑白 + 边缘噪点毛边。

    outline>0 时额外沿主体轮廓描一圈墨线，否则浅色主体（白毛、白衣服）
    在阈值化后会整块消失，只剩暗部一团黑，形状读不出来。
    """
    W, H = img.size
    lum = _lum(img)
    rng = _rng(17)
    lum = lum + (rng.random(lum.shape, dtype=np.float32) - 0.5) * rough
    on = Image.fromarray((lum < threshold).astype(np.uint8) * 255, "L")

    a = img.getchannel("A")
    bin_a = a.point(lambda v: 255 if v > 128 else 0)
    if outline and outline > 0:
        k = int(outline) * 2 + 1
        edge = ImageChops.subtract(bin_a, bin_a.filter(ImageFilter.MinFilter(k)))
        on = ImageChops.lighter(on, edge)
    alpha = ImageChops.multiply(on, bin_a)
    base = Image.new("RGBA", (W, H), _bg_color(bg))
    ink_layer = Image.new("RGBA", (W, H), tuple(ink) + (255,))
    return Image.composite(ink_layer, base, alpha)


# ------------------------------------------------------ 10 半调图案(直线)

def fx_lines(img, period=8, angle=0, ink=(30, 30, 30), bg="transparent", soft=1.5):
    """半调图案（直线）：线宽随明暗变化的单向排线。"""
    W, H = img.size
    lum = _lum(img)
    darkness = np.clip((1.0 - lum - 0.05) * soft, 0, 1)
    yy, xx = np.mgrid[0:H, 0:W]
    th = math.radians(angle)
    frac = ((xx * math.cos(th) + yy * math.sin(th)) % period) / period
    on = frac < darkness * 0.95
    cov = (on * 255).astype(np.uint8)
    alpha = ImageChops.multiply(Image.fromarray(cov, "L"), img.getchannel("A"))
    base = Image.new("RGBA", (W, H), _bg_color(bg))
    ink_layer = Image.new("RGBA", (W, H), tuple(ink) + (255,))
    return Image.composite(ink_layer, base, alpha)


# ---------------------------------------------------------------- 径向模糊

def fx_radial(img, strength=0.18, steps=36):
    """径向（放射）模糊：以画面中心为焦点做变焦拖尾。

    关键点：
    1) 必须用**预乘 alpha** 累加，否则透明区的 RGB 会渗进边缘造成灰边/白晕；
    2) steps 太小会出现同心环带，默认 36 已足够平滑。
    """
    W, H = img.size
    rgba = np.asarray(img.convert("RGBA"), dtype=np.float32)
    a0 = (rgba[..., 3:4] / 255.0)
    pre = np.concatenate([rgba[..., :3] * a0, rgba[..., 3:4]], axis=2)

    acc = np.zeros((H, W, 4), dtype=np.float32)
    cnt = np.zeros((H, W, 1), dtype=np.float32)
    for k in range(steps):
        s = 1.0 - strength * (k / (steps - 1)) if steps > 1 else 1.0
        w2, h2 = max(1, int(round(W * s))), max(1, int(round(H * s)))
        arr = np.asarray(Image.fromarray(pre.astype(np.uint8), "RGBA").resize(
            (w2, h2), Image.BILINEAR), dtype=np.float32)
        ox, oy = (W - w2) // 2, (H - h2) // 2
        acc[oy:oy + h2, ox:ox + w2] += arr
        cnt[oy:oy + h2, ox:ox + w2] += 1.0
    acc /= np.maximum(cnt, 1.0)

    out_a = np.clip(acc[..., 3], 0, 255)
    an = np.clip(out_a / 255.0, 1e-6, 1.0)
    rgb = np.clip(acc[..., :3] / an[..., None], 0, 255)
    rgb[out_a <= 1.0] = 0.0  # 全透明处 RGB 归零，避免白色残影
    out = np.concatenate([rgb, out_a[..., None]], axis=2)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- 图像描摹

def fx_trace(img, colors=6):
    """图像描摹：中位切分量化为 N 色，保留透明通道。"""
    rgb = img.convert("RGB").quantize(colors=max(2, colors), method=Image.MEDIANCUT).convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), img.getchannel("A")))


# ------------------------------------------------------------ 高斯模糊+颗粒

def fx_blurgrain(img, radius=6, grain=16, seed=23):
    r = img.convert("RGB").filter(ImageFilter.GaussianBlur(radius))
    a = img.getchannel("A").filter(ImageFilter.GaussianBlur(max(0.5, radius * 0.5)))
    arr = np.asarray(r, dtype=np.int16)
    rng = _rng(seed)
    noise = rng.integers(-grain, grain + 1, size=arr.shape[:2], dtype=np.int16)
    arr = np.clip(arr + noise[..., None], 0, 255).astype(np.uint8)
    return Image.merge("RGBA", (*Image.fromarray(arr).split(), a))


def fx_gaussian(img, radius=4):
    r = img.convert("RGB").filter(ImageFilter.GaussianBlur(radius))
    a = img.getchannel("A").filter(ImageFilter.GaussianBlur(max(0.5, radius * 0.5)))
    return Image.merge("RGBA", (*r.split(), a))


# ---------------------------------------------------------------- 玻璃

def _make_field(W, H, scale, rng):
    """平滑随机场（F 模式灰度图），两步 BICUBIC 上采样避免折痕"""
    gw, gh = max(2, W // scale), max(2, H // scale)
    coarse = rng.random((gh, gw)).astype(np.float32) * 2 - 1
    im = Image.fromarray(coarse, "F")
    mid = (max(gw * 4, 8), max(gh * 4, 8))
    im = im.resize(mid, Image.BICUBIC).resize((W, H), Image.BICUBIC)
    return im


def fx_glass(img, scale=14, strength=7, seed=31):
    """玻璃：平滑噪声折射位移 + 轻微边缘高光。"""
    W, H = img.size
    rng = _rng(seed)
    dx = np.asarray(_make_field(W, H, scale, rng), dtype=np.float32) * strength
    dy = np.asarray(_make_field(W, H, scale, rng), dtype=np.float32) * strength
    arr = np.asarray(img, dtype=np.float32)
    ch = []
    for c in range(4):
        f = arr[..., c]
        xs = np.clip(np.arange(W)[None, :] + dx, 0, W - 1)
        ys = np.clip(np.arange(H)[:, None] + dy, 0, H - 1)
        x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
        x1 = np.minimum(x0 + 1, W - 1); y1 = np.minimum(y0 + 1, H - 1)
        fx = xs - x0
        fy = ys - y0
        v = (f[y0, x0] * (1 - fx) * (1 - fy) + f[y0, x1] * fx * (1 - fy) +
             f[y1, x0] * (1 - fx) * fy + f[y1, x1] * fx * fy)
        ch.append(v)
    out = np.stack(ch, axis=2)
    # 边缘高光：位移场梯度模长（克制，避免噪感）
    gx = np.abs(np.diff(dx, axis=1, prepend=dx[:, :1]))
    gy = np.abs(np.diff(dy, axis=0, prepend=dy[:1, :]))
    edge = np.clip((gx + gy) * 6, 0, 40)
    out[..., :3] = np.clip(out[..., :3] + edge[..., None], 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- 附加

def fx_mono(img, cell=8, angle=45, ink=(17, 17, 17), bg="white", gain=1.2, ss=2):
    lum = img.convert("RGB").convert("L")
    dark = 1.0 - np.asarray(lum, dtype=np.float32) / 255.0
    dark = np.asarray(Image.fromarray((dark * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(max(1.0, cell * 0.35))), dtype=np.float32) / 255.0
    layer = _dot_layer(img.size, dark, cell, angle, gain, ss)
    cov = ImageOps.invert(layer)
    alpha = ImageChops.multiply(cov, img.getchannel("A"))
    base = Image.new("RGBA", img.size, _bg_color(bg))
    ink_layer = Image.new("RGBA", img.size, tuple(ink) + (255,))
    return Image.composite(ink_layer, base, alpha)


def fx_pixelate(img, block=12, gap=0):
    return fx_mosaic(img, block=block, grout=gap, grout_color="transparent")


# ---------------------------------------------------------------- registry

EFFECTS = {
    "halftone":    (fx_halftone,    "彩色半调",
                    "cell=8 angle_r=15 angle_g=75 angle_b=0 gain=1.15"),
    "raster":      (fx_raster,      "栅格化",        "cell=10 ink=auto|hex gain=1.25 bg=transparent|white|#hex"),
    "mezzotint":   (fx_mezzotint,   "铜版雕刻",      "density=1.0 seed=7"),
    "pointillize": (fx_pointillize, "点状化",        "dot=9 density=1.6 bg=transparent|white|#hex seed=11"),
    "crystallize": (fx_crystallize, "晶格化",        "cell=18 jitter=0.9 seed=3"),
    "mosaic":      (fx_mosaic,      "马赛克",        "block=16 grout=2 grout_color=white|transparent|#hex"),
    "glass2":      (fx_stained_glass, "染色玻璃",    "cell=20 jitter=0.9 grout_w=2 seed=5"),
    "patchwork":   (fx_patchwork,   "拼缀图",        "block=30 seam=2 shade=0.35"),
    "pen":         (fx_pen,         "绘图笔",        "period=7 angle=45 ink=#191919 bg=transparent|white|#hex soft=1.4"),
    "stamp":       (fx_stamp,       "图章",          "threshold=0.5 rough=0.08 outline=2 ink=#141414 bg=white|transparent|#hex"),
    "lines":       (fx_lines,       "半调图案(直线)", "period=8 angle=0 ink=#1e1e1e bg=transparent|white|#hex"),
    "radial":      (fx_radial,      "径向模糊",      "strength=0.18 steps=24"),
    "trace":       (fx_trace,       "图像描摹(N色)", "colors=6"),
    "blurgrain":   (fx_blurgrain,   "高斯模糊+颗粒", "radius=6 grain=16 seed=23"),
    "glass":       (fx_glass,       "玻璃",          "scale=14 strength=7 seed=31"),
    "gaussian":    (fx_gaussian,    "高斯模糊(附加)", "radius=4"),
    "mono":        (fx_mono,        "单色半调(附加)", "cell=8 angle=45 ink=hex bg=white|transparent|#hex"),
    "pixelate":    (fx_pixelate,    "像素化(附加)",  "block=12 gap=0"),
}

ALIASES = {
    "彩色半调": "halftone", "半调": "halftone", "color-halftone": "halftone",
    "栅格化": "raster", "raster": "raster", "rasterize": "raster",
    "铜版雕刻": "mezzotint", "mezzotint": "mezzotint",
    "点状化": "pointillize", "pointillize": "pointillize",
    "晶格化": "crystallize", "crystallize": "crystallize",
    "马赛克": "mosaic", "mosaic": "mosaic",
    "染色玻璃": "glass2", "stained-glass": "glass2", "stainedglass": "glass2",
    "拼缀图": "patchwork", "patchwork": "patchwork",
    "绘图笔": "pen", "graphic-pen": "pen", "pen": "pen",
    "图章": "stamp", "stamp": "stamp",
    "半调图案": "lines", "直线": "lines", "halftone-lines": "lines", "lines": "lines",
    "径向模糊": "radial", "radial": "radial", "radial-blur": "radial",
    "图像描摹": "trace", "描摹": "trace", "trace": "trace",
    "高斯模糊+颗粒": "blurgrain", "颗粒": "blurgrain", "blurgrain": "blurgrain", "grain": "blurgrain",
    "玻璃": "glass", "glass": "glass",
    "高斯模糊": "gaussian", "gaussian": "gaussian",
    "单色半调": "mono", "mono": "mono",
    "像素化": "pixelate", "pixelate": "pixelate",
}


def resolve(name):
    key = name.strip().lower()
    if key not in EFFECTS:
        for cn, en in ALIASES.items():
            if cn.lower() == key:
                key = en
                break
    if key not in EFFECTS:
        raise SystemExit(f"[djf-image-effects] 未知效果: {name}（--list 查看）")
    return key


def apply_one(img, name, params):
    key = resolve(name)
    fn, _, param_doc = EFFECTS[key]
    kwargs = {}
    for kv in params:
        k, sep, v = kv.partition("=")
        if not sep:
            raise SystemExit(f"[djf-image-effects] 参数必须为 k=v: {kv}（{key} 可用: {param_doc}）")
        if k not in param_doc:
            raise SystemExit(f"[djf-image-effects] {key} 不支持参数 {k}（可用: {param_doc}）")
        if v in ("transparent", "white", "auto") or (v.startswith("#") and len(v) == 7):
            kwargs[k] = v
        else:
            try:
                kwargs[k] = int(v)
            except ValueError:
                try:
                    kwargs[k] = float(v)
                except ValueError:
                    kwargs[k] = v
    return fn(img, **kwargs)


def apply_pipeline(img, pipeline):
    for step in [s for s in pipeline.split(";") if s.strip()]:
        name, _, rest = step.strip().partition(":")
        img = apply_one(img, name, [p for p in rest.split(",") if p])
    return img


def main():
    ap = argparse.ArgumentParser(description="主体图特效变换（Illustrator 15 效果的代码实现）")
    ap.add_argument("input", nargs="?")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--effect", nargs="+", metavar=("NAME", "k=v"))
    ap.add_argument("--pipeline", help='"gaussian:radius=3;halftone:cell=8"')
    ap.add_argument("--max-size", type=int, default=1400)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for k, (_, cn, pd) in EFFECTS.items():
            print(f"{k:12s} {cn:10s} {pd}")
        return
    if not args.input or not args.output:
        ap.error("需要 INPUT OUTPUT，或 --list")

    img = clamp_max_size(load_rgba(args.input), args.max_size or None)
    if args.pipeline:
        img = apply_pipeline(img, args.pipeline)
    elif args.effect:
        img = apply_one(img, args.effect[0], args.effect[1:])
    else:
        ap.error("必须提供 --effect 或 --pipeline")
    img.save(args.output)
    print(f"[djf-image-effects] 完成: {args.output} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
