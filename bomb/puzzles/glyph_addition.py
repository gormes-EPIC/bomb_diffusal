"""Puzzle 9 -- Glyph Addition.

The manual assigns each symbol a number.  The screen shows an equation made of
symbols; Player 1 reads it out, Player 2 looks up the values, and Player 1 types
the numeric answer.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from ..glyphs import GLYPHS, blit_glyph
from .base import Puzzle


class GlyphAddition(Puzzle):
    name = "GLYPH ADDITION"
    blurb = "Look up each symbol's value in the manual and type the total."

    def start(self):
        names = list(GLYPHS)
        for _ in range(200):
            terms = random.sample(names, random.choice([3, 3, 4]))
            ops = [random.choice(["+", "-"]) for _ in terms[1:]]
            total = GLYPHS[terms[0]].value
            for op, n in zip(ops, terms[1:]):
                total += GLYPHS[n].value if op == "+" else -GLYPHS[n].value
            if total >= 0:                 # keep answers non-negative
                break
        self.terms = terms
        self.ops = ops
        self.answer = total
        self.typed = ""
        self.wrong = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
            self.wrong = False
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.typed and int(self.typed) == self.answer:
                self.solved = True
            else:
                self.wrong = True
        elif event.unicode.isdigit():
            self.typed += event.unicode

    def draw(self, surface, area):
        self.title(surface, area)
        ui.text(surface, "Read the equation to Player 2, then type the answer "
                "and press ENTER.", area.centerx, area.y + 56, size=18,
                color=config.GREY, align="midtop")
        # Lay the equation out, fitting it to the play area: glyph [op glyph]... = ?
        items = [("g", self.terms[0])]
        for op, n in zip(self.ops, self.terms[1:]):
            items += [("op", op), ("g", n)]
        items += [("op", "="), ("box", None)]

        margin = 40
        step = min(120, (area.width - 2 * margin) / len(items))
        gsize = int(min(90, step * 0.82))
        y = area.centery - 20
        x = area.x + (area.width - step * len(items)) / 2 + step / 2
        col = config.DANGER if self.wrong else config.ACCENT
        for kind, val in items:
            if kind == "g":
                blit_glyph(surface, val, (int(x), y), gsize, config.WHITE)
            elif kind == "op":
                ui.text(surface, val, int(x), y, size=int(gsize * 0.6),
                        color=config.ACCENT, align="center", bold=True)
            else:
                box = pygame.Rect(0, 0, int(min(130, step * 1.05)), 84)
                box.center = (int(x), y)
                pygame.draw.rect(surface, (26, 30, 38), box, border_radius=8)
                pygame.draw.rect(surface, col, box, 2, border_radius=8)
                ui.text(surface, self.typed or "?", box.centerx, box.centery,
                        size=44, color=config.WHITE if self.typed else config.GREY,
                        align="center", bold=True)
            x += step
        if self.wrong:
            ui.text(surface, "Incorrect total - re-check the values.",
                    area.centerx, y + 90, size=18, color=config.DANGER,
                    align="midtop")
