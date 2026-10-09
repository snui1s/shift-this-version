#!/usr/bin/env python3
"""Turn the REAL recording in demo/demo.cast into a cinematic 1080p MP4.

Content is untouched: it is the exact output of `shift-this-version shift` that make_gif.sh
captured (including the real AI answer). Only presentation is added: a window frame on a
gradient backdrop, a virtual camera (zoom / pan), intro + outro cards, and the long burst of
output is revealed line by line (70 ms apart) so the eye can follow it.

Usage (needs demo/demo.cast from `bash demo/make_gif.sh`, plus Docker for `agg`):
    uv run --no-project --with pillow --with numpy --with imageio-ffmpeg python demo/make_video.py
    ... --preview    # write a few PNG stills instead of the full video
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
BUILD = DEMO / "_build"
STILL = "--still" in sys.argv      # GIF-friendly: no handheld drift, so held shots are truly static
CARDS = "--no-cards" not in sys.argv   # --no-cards: terminal only (no intro / outro title cards)
OUT = BUILD / "still.mp4" if STILL else DEMO / ("demo.mp4" if CARDS else "demo_terminal.mp4")

W, H, FPS, S = 1920, 1080, 30, 2          # canvas size, fps, world supersampling
WORLD_W, WORLD_H = W * S, H * S
ROWS = 34                                  # rows of the terminal that are actually used
LINE_GAP = 0.07                            # seconds between revealed lines
INTRO, OUTRO = (2.4, 3.2) if CARDS else (0.0, 0.0)   # card durations (seconds)
FONT_PX = 34                               # agg font size (high-res source for zooming)

BG_TOP, BG_BOTTOM = (12, 14, 32), (46, 22, 74)
WIN_BODY, TITLEBAR = (40, 42, 54), (33, 34, 44)


# ----------------------------------------------------------------- 1. prepare the cast
def prep_cast():
    lines = (DEMO / "demo.cast").read_text(encoding="utf-8").strip().split("\n")
    header = json.loads(lines[0])
    events = [json.loads(x) for x in lines[1:]]
    clears = [i for i, e in enumerate(events) if "\x1b[2J" in e[2]]
    scene = events[clears[0]:clears[1]]          # scene 1 = the `shift-this-version shift` run
    t0, offset = scene[0][0], 0.0
    out, marks = [], {}
    for e in scene:
        t, text = e[0] - t0 + offset, e[2]
        big = len(text) > 250 and re.search(r"Recommendation|Version Targets|UPDATED|COMMITTED|TAGGED", text)
        if big:
            parts = [p for p in re.split(r"(?<=\n)", text) if p]
            marks.setdefault("p0", t)
            for k, p in enumerate(parts):
                out.append([round(t + k * LINE_GAP, 4), "o", p])
            marks["pend"] = t + (len(parts) - 1) * LINE_GAP
            offset += (len(parts) - 1) * LINE_GAP
        else:
            out.append([round(t, 4), "o", text])
            if text == "\r\n" and "enter" not in marks and "typed" in marks:
                marks["enter"] = t
            elif len(text) == 1 and "typed" not in marks:
                marks["typed"] = t
    marks["end"] = out[-1][0]
    header.update(width=100, height=ROWS)
    with open(BUILD / "term.cast", "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        for e in out:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return marks


def render_term_gif():
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{BUILD}:/data", "ghcr.io/asciinema/agg",
         "--idle-time-limit", "100", "--font-size", str(FONT_PX), "--theme", "dracula",
         "--fps-cap", "30", "--last-frame-duration", "0.2", "/data/term.cast", "/data/term.gif"],
        check=True, capture_output=True)


# ----------------------------------------------------------------- 2. static world
def font(name, size):
    for p in (f"C:/Windows/Fonts/{name}", f"/usr/share/fonts/truetype/dejavu/{name}"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def gradient(w, h):
    y = np.linspace(0, 1, h)[:, None, None]
    top, bot = np.array(BG_TOP)[None, None, :], np.array(BG_BOTTOM)[None, None, :]
    arr = (top * (1 - y) + bot * y) * np.ones((1, w, 1))
    img = Image.fromarray(arr.astype("uint8"), "RGB")
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((-w * .15, -h * .25, w * .45, h * .55), fill=(90, 60, 200))
    d.ellipse((w * .6, h * .55, w * 1.15, h * 1.3), fill=(30, 140, 190))
    glow = glow.filter(ImageFilter.GaussianBlur(w // 8))
    return Image.blend(img, Image.fromarray(np.clip(np.asarray(img, "int16") + np.asarray(glow, "int16") // 2,
                                                    0, 255).astype("uint8")), 0.9)


def build_world(gw, gh):
    tb = 64
    term_h = int(WORLD_H * 0.86) - tb
    scale = term_h / gh
    term_w = int(gw * scale)
    win_w, win_h = term_w, term_h + tb
    wx, wy = (WORLD_W - win_w) // 2, (WORLD_H - win_h) // 2 + 10
    bg = gradient(WORLD_W, WORLD_H)

    shadow = Image.new("L", (WORLD_W, WORLD_H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((wx, wy + 40, wx + win_w, wy + win_h + 40), 36, fill=170)
    shadow = shadow.filter(ImageFilter.GaussianBlur(70))
    with_win = Image.composite(Image.new("RGB", bg.size, (0, 0, 0)), bg, shadow)

    frame = Image.new("RGB", (win_w, win_h), TITLEBAR)
    d = ImageDraw.Draw(frame)
    d.rectangle((0, tb, win_w, win_h), fill=WIN_BODY)
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        cx = 46 + i * 38
        d.ellipse((cx - 11, tb // 2 - 11, cx + 11, tb // 2 + 11), fill=c)
    title = "shift-this-version  —  ~/demo-app"
    f = font("segoeui.ttf", 26)
    d.text(((win_w - d.textlength(title, font=f)) / 2, tb / 2 - 17), title, font=f, fill=(150, 154, 175))
    mask = Image.new("L", (win_w, win_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, win_w, win_h), 36, fill=255)
    with_win.paste(frame, (wx, wy), mask)

    term_mask = mask.crop((0, tb, win_w, win_h))
    return dict(bg=bg, with_win=with_win, tb=tb, term_w=term_w, term_h=term_h, wx=wx, wy=wy,
                term_mask=term_mask)


def card(world, lines):
    """Full-canvas title card: gradient background + centered text lines [(text, font, size, color)]."""
    img = world["bg"].resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    total = sum(sz * 1.5 for _, _, sz, _ in lines)
    y = (H - total) / 2
    for text, fname, sz, color in lines:
        f = font(fname, sz)
        d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=color)
        y += sz * 1.5
    return img


# ----------------------------------------------------------------- 3. camera
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (x * 6 - 15) + 10)


def make_camera(world, keys):
    """keys: [(t, u, row, zoom)] -> function t -> (cx, cy, zoom) in canvas coordinates."""
    tb, tw, th = world["tb"], world["term_w"], world["term_h"]

    def to_canvas(u, row):
        return (world["wx"] + u * tw) / S, (world["wy"] + tb + row / ROWS * th) / S

    pts = [(t, *to_canvas(u, r), z) for t, u, r, z in keys]

    def cam(t):
        if t <= pts[0][0]:
            _, x, y, z = pts[0]
        elif t >= pts[-1][0]:
            _, x, y, z = pts[-1]
        else:
            for a, b in zip(pts, pts[1:]):
                if a[0] <= t <= b[0]:
                    k = ease((t - a[0]) / (b[0] - a[0]))
                    x, y = a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k
                    z = math.exp(math.log(a[3]) + (math.log(b[3]) - math.log(a[3])) * k)
                    break
        # gentle handheld "breathing" so held shots never feel frozen
        if STILL:
            return x, y, z
        return x + 5 * math.sin(t * 0.7), y + 3.5 * math.sin(t * 0.5), max(1.0, z * (1 + 0.006 * math.sin(t * 0.4)))
    return cam


# ----------------------------------------------------------------- 4. main
def main(preview=False):
    BUILD.mkdir(exist_ok=True)
    marks = prep_cast()
    print("marks", {k: round(v, 2) for k, v in marks.items()})
    render_term_gif()

    gif = Image.open(BUILD / "term.gif")
    gw, gh = gif.size
    world = build_world(gw, gh)
    T0 = INTRO - 0.2 if CARDS else 0.4                                     # video time at which the cast starts
    typed, enter, p0, pend, end = (T0 + marks[k] for k in ("typed", "enter", "p0", "pend", "end"))

    keys = [
        (0.0, .5, ROWS / 2, 1.00),
        (T0, .5, ROWS / 2, 1.03),                        # wide establishing shot while the window fades in
        (T0 + 2.0, .5, 10.0, 1.24),                      # slow, gentle push-in while the command is typed
        (p0 - 0.2, .5, 8.0, 1.40),                       # keep easing in as the AI answers
        (p0 + 0.8, .5, 9.5, 1.70),                       # AI Recommendation panel
        (pend + 0.9, .5, 9.7, 1.70),                     # short hold: read the reasoning
        (pend + 2.0, .5, 22.5, 1.70),                    # glide down to table + badges
        (pend + 3.8, .5, 22.7, 1.66),                    # hold on the badges (UPDATED / COMMITTED / TAGGED)
        (pend + 5.2, .5, ROWS / 2, 1.00),                # pull back to the wide shot
        (pend + 6.2, .5, ROWS / 2, 1.00),
    ]
    cam = make_camera(world, keys)
    t_outro = pend + (5.6 if CARDS else 6.0)                                  # outro crossfade starts here
    total = t_outro + OUTRO

    intro = card(world, [("Stop guessing your next version.", "segoeuib.ttf", 78, (255, 255, 255)),
                         ("Let AI read your diff and pick major, minor or patch.", "segoeui.ttf", 38, (176, 180, 215))])
    outro = card(world, [("shift-this-version", "segoeuib.ttf", 92, (255, 255, 255)),
                         ("npx shift-this-version", "consola.ttf", 54, (120, 230, 160)),
                         ("github.com/snui1s/shift-this-version", "segoeui.ttf", 34, (176, 180, 215))])

    # terminal frame timeline from the agg GIF
    frames, t = [], 0.0
    for fr in ImageSequence.Iterator(gif):
        frames.append(t)
        t += fr.info.get("duration", 40) / 1000
    gif_end = t
    gif.seek(0)

    state = {"idx": -1, "img": None}

    def term_frame(tc):
        tc = max(0.0, min(tc, gif_end - 1e-3))
        idx = max(i for i, s in enumerate(frames) if s <= tc) if tc >= frames[0] else 0
        if idx != state["idx"]:
            gif.seek(idx)
            im = gif.convert("RGB").resize((world["term_w"], world["term_h"]), Image.LANCZOS)
            state.update(idx=idx, img=im)
        return state["img"]

    def render(tv):
        win_alpha = ease((tv - (INTRO - 1.0)) / 0.8) if CARDS else 1.0
        base = world["with_win"] if win_alpha >= 1 else Image.blend(world["bg"], world["with_win"], win_alpha)
        if win_alpha > 0:
            base = base.copy()
            tf = term_frame(tv - T0)
            if win_alpha < 1:
                tf = Image.blend(Image.new("RGB", tf.size, WIN_BODY), tf, win_alpha)
            base.paste(tf, (world["wx"], world["wy"] + world["tb"]), world["term_mask"])
        cx, cy, z = cam(tv)
        bw, bh = WORLD_W / z, WORLD_H / z
        x0 = min(max(cx * S - bw / 2, 0), WORLD_W - bw)
        y0 = min(max(cy * S - bh / 2, 0), WORLD_H - bh)
        out = base.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh))
        if tv < INTRO:                                           # intro card fades out
            out = Image.blend(out, intro, 1 - ease((tv - (INTRO - 1.3)) / 1.0)) if tv > INTRO - 1.3 else intro
        if tv > t_outro:                                         # outro card fades in
            out = Image.blend(out, outro, ease((tv - t_outro) / 1.1))
        return out

    if preview:
        for name, tv in {"intro": 0.8, "type": typed + 0.8, "panel": pend + 1.8, "table": end + 2.0,
                         "wide": end + 5.4, "outro": total - 0.4}.items():
            render(tv).save(BUILD / f"preview_{name}.png")
        print("previews in", BUILD)
        return

    ff = subprocess.Popen(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        ff.stdin.write(render(i / FPS).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", OUT, f"({OUT.stat().st_size / 1e6:.1f} MB, {total:.1f}s)")


if __name__ == "__main__":
    main(preview="--preview" in sys.argv)
