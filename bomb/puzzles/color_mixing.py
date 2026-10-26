"""Puzzle 1 -- Color Mixing.

A random colour is shown on LED A (target).  Player 1 has three *unlabelled*
sliders; which slider drives which channel (R/G/B) is scrambled every game.
LED B shows the current mix.  Match LED B to LED A.  Player 2 can see both LEDs
and guides Player 1's hands.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from .base import Puzzle

TOL = 14            # per-channel tolerance for a match
HOLD = 0.4          # seconds the match must be held


class ColorMixing(Puzzle):
    name = "COLOR MIXING"
    blurb = "Match LED B to the target on LED A using the three sliders."

    def start(self):
        self.target = tuple(random.randint(40, 255) for _ in range(3))
        self.values = [random.randint(0, 255) for _ in range(3)]
        # slider i drives channel perm[i]  (0=R,1=G,2=B)
        self.perm = random.sample(range(3), 3)
        self.dragging = None
        self.match_time = 0.0
        self._geom()
        self.hw.led_a.set_color(self.target)
        self.hw.led_b.set_color(self._mix())

    def _geom(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.track_h = 300
        self.track_top = a.centery - self.track_h // 2 + 20
        gap = 150
        cx = a.centerx
        self.slider_x = [cx - gap, cx, cx + gap]

    def _mix(self):
        c = [0, 0, 0]
        for i, ch in enumerate(self.perm):
            c[ch] = self.values[i]
        return tuple(c)

    def _handle_y(self, i):
        return self.track_top + (1 - self.values[i] / 255) * self.track_h

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, x in enumerate(self.slider_x):
                if abs(event.pos[0] - x) < 40 and \
                        abs(event.pos[1] - self._handle_y(i)) < 30:
                    self.dragging = i
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = None
        elif event.type == pygame.MOUSEMOTION and self.dragging is not None:
            frac = 1 - (event.pos[1] - self.track_top) / self.track_h
            self.values[self.dragging] = int(max(0, min(1, frac)) * 255)
            self.hw.led_b.set_color(self._mix())

    def update(self, dt, inputs):
        mix = self._mix()
        if all(abs(mix[c] - self.target[c]) <= TOL for c in range(3)):
            self.match_time += dt
            if self.match_time >= HOLD:
                self.solved = True
        else:
            self.match_time = 0.0

    def draw(self, surface, area):
        self.title(surface, area)
        ui.text(surface, "Match LED B to LED A. The three sliders are unlabeled.",
                area.centerx, area.y + 56, size=18, color=config.GREY,
                align="midtop")
        for i, x in enumerate(self.slider_x):
            pygame.draw.rect(surface, (40, 46, 56),
                             (x - 5, self.track_top, 10, self.track_h),
                             border_radius=5)
            hy = self._handle_y(i)
            lit = self.match_time > 0
            col = config.OK if lit else config.LIGHT
            pygame.draw.rect(surface, col, (x - 26, hy - 11, 52, 22),
                             border_radius=6)
            pygame.draw.rect(surface, config.DARK, (x - 26, hy - 11, 52, 22),
                             2, border_radius=6)
            ui.text(surface, "?", x, self.track_top - 24, size=24,
                    color=config.GREY, align="midbottom", bold=True)
        # The LEDs live on Player 2's station (hardware panel) -- Player 1
        # cannot see them and must be guided.
        ui.text(surface, "Player 2 watches LED A (target) and LED B (yours).",
                area.centerx, self.track_top + self.track_h + 40, size=16,
                color=config.GREY, align="midtop")
