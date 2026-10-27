"""Puzzle 8 -- Symbols Lock.

Five symbols are shown; four share one hidden trait and one does not.  Player 2
has the symbol-trait table in the manual and works out which trait applies.
Player 1 clicks the odd one out.

The generator guarantees the puzzle is *unambiguous*: exactly one symbol is the
odd one out across every trait, so there is a single correct answer.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict

import pygame

from .. import config, ui
from ..glyphs import GLYPHS, TRAITS, blit_glyph
from .base import Puzzle


def _minority(names, trait):
    """Return the single odd symbol for a clean 4-1 split on ``trait``, else None."""
    if trait == "strokes":
        vals = [GLYPHS[n].strokes for n in names]
        cnt = Counter(vals)
        if sorted(cnt.values()) == [1, 4]:
            odd_val = min(cnt, key=lambda v: cnt[v])
            return names[vals.index(odd_val)]
        return None
    vals = [getattr(GLYPHS[n], trait) for n in names]
    if vals.count(True) == 1:
        return names[vals.index(True)]
    if vals.count(False) == 1:
        return names[vals.index(False)]
    return None


def make_symbol_puzzle(rng=random):
    names = list(GLYPHS)
    for _ in range(4000):
        trait = rng.choice(list(TRAITS))
        if trait == "strokes":
            groups = defaultdict(list)
            for n in names:
                groups[GLYPHS[n].strokes].append(n)
            big = [v for v in groups.values() if len(v) >= 4]
            if not big:
                continue
            share = rng.choice(big)
            four = rng.sample(share, 4)
            odd_pool = [n for n in names if n not in share]
        else:
            trues = [n for n in names if getattr(GLYPHS[n], trait)]
            falses = [n for n in names if not getattr(GLYPHS[n], trait)]
            if len(trues) >= 4 and falses:
                four, odd_pool = rng.sample(trues, 4), falses
            elif len(falses) >= 4 and trues:
                four, odd_pool = rng.sample(falses, 4), trues
            else:
                continue
        if not odd_pool:
            continue
        odd = rng.choice(odd_pool)
        chosen = four + [odd]
        odds = {m for tr in TRAITS if (m := _minority(chosen, tr)) is not None}
        if odds == {odd}:
            rng.shuffle(chosen)
            return {"symbols": chosen, "odd": odd, "trait": trait}
    raise RuntimeError("could not build an unambiguous symbol puzzle")


class SymbolsLock(Puzzle):
    name = "SYMBOLS LOCK"
    blurb = "Four symbols share a hidden trait. Click the one that doesn't."

    def start(self):
        p = make_symbol_puzzle()
        self.symbols = p["symbols"]
        self.odd = p["odd"]
        self.wrong = None
        self._geom()

    def _geom(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.box = 150
        n = len(self.symbols)
        gap = 40
        total = n * self.box + (n - 1) * gap
        sx = a.centerx - total // 2
        self.rects = [pygame.Rect(sx + i * (self.box + gap),
                                  a.centery - self.box // 2, self.box, self.box)
                      for i in range(n)]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(event.pos):
                    if self.symbols[i] == self.odd:
                        self.solved = True
                    elif i != self.wrong:
                        self.wrong = i
                        self.strike()

    def draw(self, surface, area):
        for i, r in enumerate(self.rects):
            border = config.DANGER if i == self.wrong else (60, 66, 76)
            pygame.draw.rect(surface, (26, 30, 38), r, border_radius=10)
            pygame.draw.rect(surface, border, r, 2, border_radius=10)
            blit_glyph(surface, self.symbols[i], r.center, self.box - 40,
                       config.WHITE)
        if self.wrong is not None:
            ui.text(surface, "That one fits the group - look again.",
                    area.centerx, self.rects[0].bottom + 30, size=18,
                    color=config.DANGER, align="midtop")
