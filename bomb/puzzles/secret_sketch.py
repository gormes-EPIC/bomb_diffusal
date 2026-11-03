"""Puzzle 12 -- Secret Sketch.

Player 1 sees a list of line segments -- pairs of (x, y) grid points -- and reads
them out.  Player 2 plots each segment on the blank coordinate grid in the
manual; joined up, the segments draw a simple picture (a star, a rocket, a
house...).  Player 2 recognises it and tells Player 1 what it is; Player 1 types
the word.  Neither can do it alone: Player 1 has the numbers, Player 2 has the
grid.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from ..puzzle_data import SKETCHES
from .base import Puzzle


def _fmt(v) -> str:
    """Grid value as text: 18 -> '18', 3.5 -> '3.5'."""
    return str(int(v)) if float(v).is_integer() else str(v)


class SecretSketch(Puzzle):
    name = "SECRET SKETCH"
    blurb = "Read the segment coordinates to Player 2, who plots the picture."

    def start(self):
        self.sketch = random.choice(SKETCHES)
        self.word = self.sketch["name"]
        self.segments = self.sketch["segments"]
        self.typed = ""
        self.wrong = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
            self.wrong = False
        elif event.unicode and event.unicode.isalpha():
            if len(self.typed) < len(self.word):
                self.typed += event.unicode.upper()
                if len(self.typed) == len(self.word):
                    if self.typed == self.word:
                        self.solved = True
                    else:
                        self.wrong = True
                        self.strike()

    def update(self, dt, inputs):
        pass

    # ------------------------------------------------------------------ draw
    def draw(self, surface, area):
        cx = area.centerx
        ui.text(surface, "PLOT THE SEGMENTS", cx, area.y + 22, size=36,
                color=config.ACCENT, align="midtop", bold=True)

        bottom = self._draw_segments(surface, area)
        self._draw_answer(surface, area, bottom)

    def _draw_segments(self, surface, area):
        lines = [f"{i + 1:>2}.  ({_fmt(a[0])}, {_fmt(a[1])})  →  "
                 f"({_fmt(b[0])}, {_fmt(b[1])})"
                 for i, (a, b) in enumerate(self.segments)]
        top = area.y + 120
        gap = 46
        if len(lines) <= 8:
            for i, ln in enumerate(lines):
                ui.text(surface, ln, area.centerx, top + i * gap, size=28,
                        color=config.WHITE, align="midtop", mono=True)
            return top + len(lines) * gap
        # Two columns for longer lists.
        half = (len(lines) + 1) // 2
        col_x = (area.centerx - 460, area.centerx + 50)
        for i, ln in enumerate(lines):
            col = 0 if i < half else 1
            row = i if col == 0 else i - half
            ui.text(surface, ln, col_x[col], top + row * gap, size=26,
                    color=config.WHITE, align="topleft", mono=True)
        return top + half * gap

    def _draw_answer(self, surface, area, top):
        n = len(self.word)
        slot = 56
        sx = area.centerx - n * slot // 2
        y = top + 40
        for i in range(n):
            x = sx + i * slot + slot // 2
            pygame.draw.line(surface, config.LIGHT, (x - 20, y + 24),
                             (x + 20, y + 24), 3)
            ch = self.typed[i] if i < len(self.typed) else ""
            col = config.DANGER if self.wrong else config.WHITE
            ui.text(surface, ch, x, y, size=46, color=col, align="center",
                    bold=True)
        if self.wrong:
            ui.text(surface, "Not quite - backspace and retry.", area.centerx,
                    y + 54, size=18, color=config.DANGER, align="midtop")
