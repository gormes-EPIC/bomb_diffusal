"""Vector-drawn symbols ("glyphs") used by the symbol puzzles.

Each glyph is drawn with pygame primitives (never a font) so that it looks
identical in the running game and in the PNGs baked into Player 2's manual, and
so that its *traits* (stroke count, curved/straight, symmetrical, closed) are a
property we control exactly rather than guess from a font character.

A single catalogue, ``GLYPHS``, is the one source of truth.  Puzzle 8 (Symbols
Lock) and Puzzle 9 (Glyph Addition) read it, and ``tools/generate_manuals.py``
reads it to build the manual's symbol tables and PNGs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import pygame


@dataclass(frozen=True)
class Glyph:
    name: str
    draw_fn: Callable          # (surf, size, color, width) -> None
    strokes: int               # pen strokes to draw it (manual data)
    curved: bool               # made of curves rather than straight lines
    symmetrical: bool          # has at least one mirror axis
    closed: bool               # encloses an area
    value: int                 # numeric value for Puzzle 9


# --------------------------------------------------------------------------- #
# Low-level drawing helpers.  Each draws centred inside a size x size box on a
# per-pixel-alpha surface.
# --------------------------------------------------------------------------- #
def _poly(points, surf, color, w):
    pygame.draw.polygon(surf, color, points, w)


def _regular(cx, cy, r, n, start_deg=-90):
    pts = []
    for k in range(n):
        a = math.radians(start_deg + k * 360 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_circle(surf, S, color, w):
    pygame.draw.circle(surf, color, (S // 2, S // 2), int(S * 0.36), w)


def draw_square(surf, S, color, w):
    rect = pygame.Rect(0, 0, int(S * 0.62), int(S * 0.62))
    rect.center = (S // 2, S // 2)
    pygame.draw.rect(surf, color, rect, w, border_radius=2)


def draw_triangle(surf, S, color, w):
    _poly(_regular(S // 2, S // 2 + S * 0.04, S * 0.40, 3), surf, color, w)


def draw_pentagon(surf, S, color, w):
    _poly(_regular(S // 2, S // 2, S * 0.40, 5), surf, color, w)


def draw_star(surf, S, color, w):
    cx, cy = S / 2, S / 2
    outer, inner = S * 0.42, S * 0.17
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        r = outer if k % 2 == 0 else inner
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    _poly(pts, surf, color, w)


def draw_plus(surf, S, color, w):
    cx, cy = S / 2, S / 2
    a = S * 0.40       # arm half-length
    t = S * 0.13       # arm half-thickness
    pts = [
        (cx - t, cy - a), (cx + t, cy - a), (cx + t, cy - t), (cx + a, cy - t),
        (cx + a, cy + t), (cx + t, cy + t), (cx + t, cy + a), (cx - t, cy + a),
        (cx - t, cy + t), (cx - a, cy + t), (cx - a, cy - t), (cx - t, cy - t),
    ]
    _poly(pts, surf, color, w)


def draw_arrow(surf, S, color, w):
    cx, cy = S / 2, S / 2
    # Points right.  Shaft + head, as a closed outline.
    pts = [
        (cx - S * 0.34, cy - S * 0.12), (cx + S * 0.04, cy - S * 0.12),
        (cx + S * 0.04, cy - S * 0.26), (cx + S * 0.38, cy),
        (cx + S * 0.04, cy + S * 0.26), (cx + S * 0.04, cy + S * 0.12),
        (cx - S * 0.34, cy + S * 0.12),
    ]
    _poly(pts, surf, color, w)


def draw_heart(surf, S, color, w):
    cx, cy = S / 2, S / 2
    r = S * 0.17
    pygame.draw.circle(surf, color, (int(cx - r * 0.95), int(cy - r * 0.55)), int(r))
    pygame.draw.circle(surf, color, (int(cx + r * 0.95), int(cy - r * 0.55)), int(r))
    pygame.draw.polygon(surf, color, [
        (cx - r * 1.95, cy - r * 0.25), (cx + r * 1.95, cy - r * 0.25),
        (cx, cy + r * 2.25),
    ])


def draw_crescent(surf, S, color, w):
    # Filled lune: an opaque disk with an offset disk erased out of it.
    cx, cy = S // 2, S // 2
    R = int(S * 0.38)
    pygame.draw.circle(surf, color, (cx, cy), R)
    # Drawing a fully transparent colour onto a per-pixel-alpha surface
    # replaces (does not blend) those pixels, carving the bite out.
    pygame.draw.circle(surf, (0, 0, 0, 0), (int(cx + R * 0.55), cy - int(R * 0.1)), R)


def draw_spiral(surf, S, color, w):
    cx, cy = S / 2, S / 2
    pts = []
    turns = 2.6
    steps = 120
    for i in range(steps + 1):
        t = i / steps
        a = t * turns * 2 * math.pi
        r = t * S * 0.40
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.lines(surf, color, False, pts, w)


# --------------------------------------------------------------------------- #
# The catalogue.  Order matters only for stable manual output.
# --------------------------------------------------------------------------- #
GLYPHS: dict[str, Glyph] = {
    g.name: g for g in [
        #       name        draw_fn        strokes curved  symm   closed value
        Glyph("spiral",   draw_spiral,   1, True,  False, False, 1),
        Glyph("circle",   draw_circle,   1, True,  True,  True,  2),
        Glyph("crescent", draw_crescent, 2, True,  False, True,  3),
        Glyph("square",   draw_square,   4, False, True,  True,  4),
        Glyph("triangle", draw_triangle, 3, False, True,  True,  5),
        Glyph("pentagon", draw_pentagon, 5, False, True,  True,  6),
        Glyph("star",     draw_star,     5, False, True,  True,  7),
        Glyph("heart",    draw_heart,    3, True,  True,  True,  8),
        Glyph("arrow",    draw_arrow,    3, False, True,  False, 9),
        Glyph("plus",     draw_plus,     3, False, True,  False, 10),
    ]
}

# Glyphs with no rotational symmetry -- used by Puzzle 10 (Rotation Lock) so a
# rotation is actually visible.
ROTATION_GLYPHS = ["arrow", "spiral", "crescent"]

# The four traits Puzzle 8 can key on, with human labels for the manual.
TRAITS = {
    "strokes": "Same number of strokes",
    "curved": "All curved (no straight edges)",
    "symmetrical": "All symmetrical (have a mirror line)",
    "closed": "All closed shapes (fully enclose an area)",
}


def render_glyph(name: str, size: int, color, rotation: float = 0.0,
                 width: int | None = None) -> pygame.Surface:
    """Return a (possibly rotated) per-pixel-alpha surface for a glyph."""
    g = GLYPHS[name]
    if width is None:
        width = max(3, size // 14)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    g.draw_fn(surf, size, color, width)
    if rotation:
        surf = pygame.transform.rotate(surf, rotation)
    return surf


def blit_glyph(target: pygame.Surface, name: str, center, size: int, color,
               rotation: float = 0.0, width: int | None = None):
    surf = render_glyph(name, size, color, rotation, width)
    rect = surf.get_rect(center=center)
    target.blit(surf, rect)
