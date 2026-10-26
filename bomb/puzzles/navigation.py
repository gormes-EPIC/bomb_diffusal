"""Puzzle 5 -- Navigation.

The screen lists turn-by-turn trail directions.  Player 1 reads them out;
Player 2 traces them on the manual's map with a ruler and protractor and names
the landmark where the trail ends.  Player 1 clicks (or presses) that landmark.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from ..puzzle_data import NAV_ANSWERS, NAV_LANDMARKS, NAV_NAMES, ROUTES, \
    route_instructions
from .base import Puzzle


class Navigation(Puzzle):
    name = "NAVIGATION"
    blurb = "Follow the directions on the map; pick the final landmark."

    def start(self):
        self.index = random.randrange(len(ROUTES))
        self.lines = route_instructions(ROUTES[self.index])
        self.answer = NAV_ANSWERS[self.index]
        self.letters = sorted(NAV_LANDMARKS.keys())
        self.wrong = None
        self._geom()

    def _geom(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.buttons = {}
        per_row = 4
        bw, bh, gap = 150, 56, 18
        rows = (len(self.letters) + per_row - 1) // per_row
        total_w = per_row * bw + (per_row - 1) * gap
        sx = a.centerx - total_w // 2
        sy = a.bottom - rows * (bh + gap) - 20
        for i, L in enumerate(self.letters):
            r, c = divmod(i, per_row)
            self.buttons[L] = pygame.Rect(sx + c * (bw + gap),
                                          sy + r * (bh + gap), bw, bh)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for L, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    self._choose(L)
        elif event.type == pygame.KEYDOWN and event.unicode:
            L = event.unicode.upper()
            if L in self.buttons:
                self._choose(L)

    def _choose(self, L):
        if L == self.answer:
            self.solved = True
        else:
            self.wrong = L

    def draw(self, surface, area):
        # The directions ARE the puzzle, so they stay. No title, no how-to.
        y = area.y + 50
        for line in self.lines:
            ui.text(surface, line, area.centerx, y, size=22, color=config.LIGHT,
                    align="midtop")
            y += 34
        for L, rect in self.buttons.items():
            bad = (L == self.wrong)
            col = config.DANGER if bad else (46, 52, 62)
            pygame.draw.rect(surface, col, rect, border_radius=8)
            pygame.draw.rect(surface, config.GREY, rect, 1, border_radius=8)
            ui.text(surface, f"{L}", rect.centerx, rect.centery - 8, size=22,
                    color=config.WHITE, align="center", bold=True)
            ui.text(surface, NAV_NAMES[L], rect.centerx, rect.bottom - 6, size=12,
                    color=config.GREY, align="midbottom")
        if self.wrong:
            ui.text(surface, "Not there - re-check the bearings and distances.",
                    area.centerx, area.bottom - 8, size=16, color=config.DANGER,
                    align="midbottom")
