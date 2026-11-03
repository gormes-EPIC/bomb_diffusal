#!/usr/bin/env python3
"""Generate the two manuals (and their image assets) from puzzle_data + glyphs.

Run from the project root:

    python tools/generate_manuals.py

Writes:
    docs/player1_decoder_cards.md
    docs/player2_manual.md
    docs/assets/*.png

Because everything is rendered from the same source of truth the program uses,
the printed manuals always match the running bomb.
"""

from __future__ import annotations

import math
import os
import sys

# Allow "import bomb..." when run from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from bomb import puzzle_data as pd  # noqa: E402
from bomb.glyphs import GLYPHS, render_glyph  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
ASSETS = os.path.join(DOCS, "assets")

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
INK = (25, 25, 25)
GREYINK = (120, 120, 120)
WALL = (30, 30, 30)
GREEN = (30, 150, 70)
RED = (200, 50, 50)
BLUE = (40, 90, 190)

pygame.init()
pygame.font.init()


def _font(size, bold=False):
    return pygame.font.SysFont("dejavusans,arial", size, bold=bold)


def _text(surf, s, x, y, size=20, color=INK, align="topleft", bold=False):
    img = _font(size, bold).render(str(s), True, color)
    r = img.get_rect()
    setattr(r, align, (x, y))
    surf.blit(img, r)


def save(surf, name):
    pygame.image.save(surf, os.path.join(ASSETS, name))
    return "assets/" + name


# --------------------------------------------------------------------------- #
# Glyph images (black ink on white)
# --------------------------------------------------------------------------- #
def render_glyph_png(name, size=120):
    surf = pygame.Surface((size, size))
    surf.fill(WHITE)
    g = render_glyph(name, size, BLACK, width=max(4, size // 14))
    surf.blit(g, (0, 0))
    return save(surf, f"sym_{name}.png")


# --------------------------------------------------------------------------- #
# Maze images (walls shown -- this is Player 2's secret map)
# --------------------------------------------------------------------------- #
def render_maze_png(index):
    maze = pd.get_maze(index)
    w, h = maze["w"], maze["h"]
    cell = 64
    pad = 30
    W = w * cell + pad * 2
    H = h * cell + pad * 2 + 30
    surf = pygame.Surface((W, H))
    surf.fill(WHITE)
    _text(surf, f"Maze {index + 1}", W // 2, 6, 22, INK, "midtop", bold=True)

    def px(cx, cy):
        return pad + cx * cell, 30 + pad + cy * cell

    # draw walls: for each cell, a side is a wall if not open
    for y in range(h):
        for x in range(w):
            opens = maze["cells"][y][x]
            x0, y0 = px(x, y)
            x1, y1 = x0 + cell, y0 + cell
            if "N" not in opens:
                pygame.draw.line(surf, WALL, (x0, y0), (x1, y0), 4)
            if "W" not in opens:
                pygame.draw.line(surf, WALL, (x0, y0), (x0, y1), 4)
            if "S" not in opens:
                pygame.draw.line(surf, WALL, (x0, y1), (x1, y1), 4)
            if "E" not in opens:
                pygame.draw.line(surf, WALL, (x1, y0), (x1, y1), 4)
    # start + goal
    sx, sy = px(*maze["start"])
    gx, gy = px(*maze["goal"])
    pygame.draw.circle(surf, RED, (sx + cell // 2, sy + cell // 2), cell // 4)
    _text(surf, "start", sx + cell // 2, sy + cell // 2 + 16, 13, RED, "midtop")
    pygame.draw.rect(surf, GREEN,
                     (gx + cell // 4, gy + cell // 4, cell // 2, cell // 2))
    _text(surf, "GOAL", gx + cell // 2, gy + 4, 13, GREEN, "midtop")
    return save(surf, f"maze_{index + 1}.png")


# --------------------------------------------------------------------------- #
# Navigation map (landmarks only -- the trail is secret, players trace it)
# --------------------------------------------------------------------------- #
def render_nav_map_png():
    scale = 52           # pixels per mile
    pad = 46
    xs = [v[0] for v in pd.NAV_LANDMARKS.values()] + [pd.NAV_START[0]]
    ys = [v[1] for v in pd.NAV_LANDMARKS.values()] + [pd.NAV_START[1]]
    minx, maxx = min(xs) - 1, max(xs) + 1
    miny, maxy = min(ys) - 1, max(ys) + 1
    W = int((maxx - minx) * scale) + pad * 2
    H = int((maxy - miny) * scale) + pad * 2
    surf = pygame.Surface((W, H))
    surf.fill(WHITE)

    def px(mx, my):
        return (int(pad + (mx - minx) * scale), int(pad + (my - miny) * scale))

    # 1-mile grid
    for mx in range(int(minx), int(maxx) + 1):
        x, _ = px(mx, miny)
        pygame.draw.line(surf, (225, 225, 225), (x, pad), (x, H - pad), 1)
    for my in range(int(miny), int(maxy) + 1):
        _, y = px(minx, my)
        pygame.draw.line(surf, (225, 225, 225), (pad, y), (W - pad, y), 1)
    pygame.draw.rect(surf, (180, 180, 180), (pad, pad, W - 2 * pad, H - 2 * pad), 2)

    # start marker
    s = px(*pd.NAV_START)
    pygame.draw.polygon(surf, BLUE, [(s[0], s[1] - 11), (s[0] - 10, s[1] + 8),
                                     (s[0] + 10, s[1] + 8)])
    _text(surf, "TRAILHEAD", s[0], s[1] + 10, 13, BLUE, "midtop", bold=True)

    # landmarks
    for L, (mx, my) in pd.NAV_LANDMARKS.items():
        p = px(mx, my)
        pygame.draw.circle(surf, INK, p, 7)
        pygame.draw.circle(surf, WHITE, p, 3)
        _text(surf, L, p[0] + 10, p[1] - 10, 20, INK, "topleft", bold=True)
        _text(surf, pd.NAV_NAMES[L], p[0] + 10, p[1] + 8, 12, GREYINK, "topleft")

    # north arrow
    nx, ny = W - pad - 24, pad + 36
    pygame.draw.line(surf, INK, (nx, ny + 24), (nx, ny - 20), 3)
    pygame.draw.polygon(surf, INK, [(nx, ny - 28), (nx - 7, ny - 14),
                                    (nx + 7, ny - 14)])
    _text(surf, "N", nx, ny - 48, 18, INK, "midtop", bold=True)

    # scale bar (1 mile)
    bx, by = pad, H - pad + 14
    pygame.draw.line(surf, INK, (bx, by), (bx + scale, by), 3)
    pygame.draw.line(surf, INK, (bx, by - 4), (bx, by + 4), 3)
    pygame.draw.line(surf, INK, (bx + scale, by - 4), (bx + scale, by + 4), 3)
    _text(surf, "1 mile", bx + scale + 8, by - 9, 13, INK, "topleft")
    return save(surf, "nav_map.png")


# --------------------------------------------------------------------------- #
# Logic circuits (gate types LABELLED -- the manual's secret)
# --------------------------------------------------------------------------- #
def render_circuit_png(circuit):
    W, H = 560, 300
    surf = pygame.Surface((W, H))
    surf.fill(WHITE)
    m = 26
    inner = pygame.Rect(m, m, W - 2 * m, H - 2 * m)
    _text(surf, f"Circuit {circuit['id']}", W // 2, 4, 20, INK, "midtop", bold=True)

    pos = {}
    for name, (nx, ny) in circuit["inputs"].items():
        pos[name] = (inner.x + nx * inner.w, inner.y + ny * inner.h)
    for g in circuit["gates"]:
        gx, gy = g["pos"]
        pos[g["id"]] = (inner.x + gx * inner.w, inner.y + gy * inner.h)
    lamp = (inner.right - 6, inner.y + 0.5 * inner.h)

    # wires
    for g in circuit["gates"]:
        for ref in g["in"]:
            pygame.draw.line(surf, (90, 90, 90), pos[ref], pos[g["id"]], 2)
    pygame.draw.line(surf, (90, 90, 90), pos[circuit["output"]], lamp, 2)

    # inputs
    for name in circuit["inputs"]:
        p = pos[name]
        pygame.draw.circle(surf, (235, 235, 235), (int(p[0]), int(p[1])), 18)
        pygame.draw.circle(surf, INK, (int(p[0]), int(p[1])), 18, 2)
        _text(surf, name.upper(), int(p[0]) - 24, int(p[1]), 15, INK, "midright")

    # gates (labelled with type AND numbered as on screen)
    for i, g in enumerate(circuit["gates"], 1):
        p = pos[g["id"]]
        r = pygame.Rect(0, 0, 90, 54)
        r.center = (int(p[0]), int(p[1]))
        pygame.draw.rect(surf, (240, 240, 240), r, border_radius=6)
        pygame.draw.rect(surf, INK, r, 2, border_radius=6)
        _text(surf, g["type"], r.centerx, r.centery - 10, 20, INK, "center", bold=True)
        _text(surf, f"(box {i})", r.centerx, r.centery + 10, 12, GREYINK, "center")

    # output lamp
    pygame.draw.circle(surf, (250, 210, 60), (int(lamp[0]), int(lamp[1])), 16)
    pygame.draw.circle(surf, INK, (int(lamp[0]), int(lamp[1])), 16, 2)
    _text(surf, "OUT", int(lamp[0]), int(lamp[1]) + 18, 13, INK, "midtop")
    return save(surf, f"circuit_{circuit['id'].lower()}.png")


# --------------------------------------------------------------------------- #
# Wire-scrambler junction boxes (the hidden internal wiring -- Player 2's secret)
# --------------------------------------------------------------------------- #
def render_scramble_box_png(name, perm):
    n = len(perm)
    pad = 36
    row = 40
    W, H = 300, pad + 24 + (n - 1) * row + 54
    surf = pygame.Surface((W, H))
    surf.fill(WHITE)
    _text(surf, f"Box {name}", W // 2, 6, 20, INK, "midtop", bold=True)

    lx, rx = 70, W - 70
    top = pad + 24

    def py(i):
        return top + i * row

    # connecting lines first (so the ports sit on top)
    for i, j in enumerate(perm):
        pygame.draw.line(surf, (150, 150, 150), (lx, py(i)), (rx, py(j)), 2)

    for i in range(n):
        # left port, with its destination number spelled out for fast lookup
        pygame.draw.circle(surf, (235, 235, 235), (lx, py(i)), 13)
        pygame.draw.circle(surf, INK, (lx, py(i)), 13, 2)
        _text(surf, str(i + 1), lx, py(i), 15, INK, "center", bold=True)
        _text(surf, f"→ {perm[i] + 1}", lx - 22, py(i), 14, GREYINK,
              "midright")
        # right port
        pygame.draw.circle(surf, (235, 235, 235), (rx, py(i)), 13)
        pygame.draw.circle(surf, INK, (rx, py(i)), 13, 2)
        _text(surf, str(i + 1), rx, py(i), 15, INK, "center", bold=True)

    _text(surf, "left → right", W // 2, py(n - 1) + 28, 12, GREYINK,
          "midtop")
    return save(surf, f"scramble_box_{name}.png")


# --------------------------------------------------------------------------- #
# Secret Sketch -- a blank coordinate grid for Player 2 to plot on
# --------------------------------------------------------------------------- #
def render_sketch_grid_png():
    G = pd.SKETCH_GRID
    cell = 30
    pad = 46
    size = G * cell
    W = H = size + pad * 2
    surf = pygame.Surface((W, H))
    surf.fill(WHITE)

    def px(x, y):
        return (pad + x * cell, pad + (G - y) * cell)   # y upward

    for i in range(G + 1):
        major = i % 5 == 0
        c = (90, 90, 90) if major else (205, 205, 205)
        wdt = 2 if major else 1
        pygame.draw.line(surf, c, px(0, i), px(G, i), wdt)       # horizontals
        pygame.draw.line(surf, c, px(i, 0), px(i, G), wdt)       # verticals
        if major:
            _text(surf, str(i), px(i, 0)[0], H - pad + 8, 15, INK, "midtop")
            _text(surf, str(i), pad - 10, px(0, i)[1], 15, INK, "midright")
    # axis labels
    _text(surf, "x", W - pad + 18, H - pad, 18, INK, "midleft", bold=True)
    _text(surf, "y", pad, pad - 26, 18, INK, "midtop", bold=True)
    return save(surf, "sketch_grid.png")


# --------------------------------------------------------------------------- #
# Markdown writers
# --------------------------------------------------------------------------- #
HEADER_NOTE = ("<!-- GENERATED by tools/generate_manuals.py from bomb/puzzle_data.py"
               " and bomb/glyphs.py. Do not edit by hand; re-run the generator. -->\n\n")


def write_player1(glyph_imgs):
    # Player 1's reference cards. Only the lookup data -- no puzzle names, no
    # descriptions of how the modules work (that is for the players to figure
    # out). Keep Player 1's manual separate from Player 2's.
    out = [HEADER_NOTE]
    w = out.append
    w("# Player 1\n")

    # ---- Morse ----
    w("\n## Morse Code\n")
    letters = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    w("\n| Ltr | Code | Ltr | Code | Ltr | Code |")
    w("| --- | --- | --- | --- | --- | --- |")
    for i in range(0, 26, 3):
        row = []
        for j in range(3):
            if i + j < 26:
                L = letters[i + j]
                row += [f"**{L}**", f"`{pd.MORSE[L]}`"]
            else:
                row += ["", ""]
        w("| " + " | ".join(row) + " |")

    # ---- Colour translation ----
    w("\n## Think Fast!\n")
    w("\n| Color | Press |")
    w("| --- | --- |")
    for shown, presses in pd.SIMON_RULES.items():
        pretty = " + ".join(p.capitalize() for p in presses)
        w(f"| {shown.capitalize()} | {pretty} |")
    w("")
    _write(os.path.join(DOCS, "player1_decoder_cards.md"), out)


def write_player2(glyph_imgs, maze_imgs, nav_img, scramble_imgs, sketch_img):
    # Player 2's reference data only: the mazes, the map, the symbol tables and
    # the scrambler junction boxes. No puzzle names and no how-to narration.
    out = [HEADER_NOTE]
    w = out.append
    w("# Player 2\n")
    w("You should also have paper/pencil, and a ruler.\n")
    
    # ---- Mazes ----
    w("\n## Mazes\n")
    for i, img in enumerate(maze_imgs):
        w(f"\n![Maze {i + 1}]({img})\n")

    # ---- Trail map ----
    w("\n## Trail Map\n")
    w(f"\n![Trail map]({nav_img})\n")

    # ---- Symbol values ----
    w("\n## Symbol Values\n")
    w("\n| Symbol | Name | Value | | Symbol | Name | Value |")
    w("| :---: | --- | :---: | --- | :---: | --- | :---: |")
    names = list(GLYPHS)
    for i in range(0, len(names), 2):
        a = names[i]
        cells = [f"![]({glyph_imgs[a]})", a.capitalize(), str(GLYPHS[a].value), ""]
        if i + 1 < len(names):
            b = names[i + 1]
            cells += [f"![]({glyph_imgs[b]})", b.capitalize(), str(GLYPHS[b].value)]
        else:
            cells += ["", "", ""]
        w("| " + " | ".join(cells) + " |")

    # ---- Wire-scrambler junction boxes ----
    w("\n## Junction Boxes\n")
    for name in pd.SCRAMBLE_BOXES:
        w(f"\n![Box {name}]({scramble_imgs[name]})\n")

    # ---- Secret Sketch coordinate grid ----
    w("\n## Coordinate Grid\n")
    w("Plot each segment Player 1 reads as a point `(x, y)` joined to the next, "
      "then read off the picture they draw. (x across, y up.)\n")
    w(f"\n![Coordinate grid]({sketch_img})\n")

    _write(os.path.join(DOCS, "player2_manual.md"), out)


def _write(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print("wrote", os.path.relpath(path, ROOT))


def main():
    os.makedirs(ASSETS, exist_ok=True)
    glyph_imgs = {name: render_glyph_png(name) for name in GLYPHS}
    maze_imgs = [render_maze_png(i) for i in range(pd.maze_count())]
    nav_img = render_nav_map_png()
    # The logic-gates circuit puzzle is retired: render_circuit_png and the
    # CIRCUITS data are kept, but no circuit images or manual section are made.
    scramble_imgs = {name: render_scramble_box_png(name, perm)
                     for name, perm in pd.SCRAMBLE_BOXES.items()}
    sketch_img = render_sketch_grid_png()
    write_player1(glyph_imgs)
    write_player2(glyph_imgs, maze_imgs, nav_img, scramble_imgs, sketch_img)
    print(f"assets: {len(glyph_imgs)} glyphs, {len(maze_imgs)} mazes, "
          f"1 map, {len(scramble_imgs)} boxes, 1 sketch grid")


if __name__ == "__main__":
    main()
