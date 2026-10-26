"""Puzzle 10 -- Rotation Lock.

The screen shows a reference symbol and a copy that Player 2 rotates with the
rotary encoder.  Line the copy up with the reference and hold it for three
rounds, each within a time limit.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from ..glyphs import ROTATION_GLYPHS, blit_glyph
from .base import Puzzle

STEP = 15            # degrees per encoder detent
TOL = 8              # match tolerance (degrees)
HOLD = 0.5          # seconds to hold a match
ROUND_TIME = 30.0   # soft per-round time limit
ROUNDS = 3


def _ang_diff(a, b):
    return abs((a - b + 180) % 360 - 180)


class RotationLock(Puzzle):
    name = "ROTATION LOCK"
    blurb = "Spin the encoder to line up the symbol. Three rounds."

    def start(self):
        self.round = 0
        self._new_round()

    def _new_round(self):
        self.glyph = random.choice(ROTATION_GLYPHS)
        self.ref_angle = random.randrange(0, 360, STEP)
        offset = random.choice([a for a in range(STEP, 360, STEP)])
        self.cur_angle = (self.ref_angle + offset) % 360
        self.hold = 0.0
        self.time_left = ROUND_TIME

    def update(self, dt, inputs):
        if inputs.encoder_delta:
            # Clockwise detent rotates the symbol clockwise (negative in pygame).
            self.cur_angle = (self.cur_angle - inputs.encoder_delta * STEP) % 360

        matched = _ang_diff(self.cur_angle, self.ref_angle) <= TOL
        if matched:
            self.hold += dt
            if self.hold >= HOLD:
                self.round += 1
                if self.round >= ROUNDS:
                    self.solved = True
                else:
                    self._new_round()
                return
        else:
            self.hold = 0.0

        self.time_left -= dt
        if self.time_left <= 0:         # soft reset, not a game-over
            self._new_round()

    def draw(self, surface, area):
        self.title(surface, area)
        ui.text(surface, f"ROUND {min(self.round + 1, ROUNDS)} / {ROUNDS}  -  "
                "Player 2 spins the encoder to match the symbols.",
                area.centerx, area.y + 56, size=18, color=config.GREY,
                align="midtop")
        matched = _ang_diff(self.cur_angle, self.ref_angle) <= TOL
        gs = 160
        cy = area.centery
        ui.text(surface, "REFERENCE", area.centerx - 160, cy - 130, size=15,
                color=config.GREY, align="center")
        blit_glyph(surface, self.glyph, (area.centerx - 160, cy), gs,
                   config.LIGHT, rotation=self.ref_angle)
        ui.text(surface, "YOURS", area.centerx + 160, cy - 130, size=15,
                color=config.GREY, align="center")
        blit_glyph(surface, self.glyph, (area.centerx + 160, cy), gs,
                   config.OK if matched else config.WARN, rotation=self.cur_angle)

        # round timer bar
        barw = 360
        bx = area.centerx - barw // 2
        by = cy + 150
        pygame.draw.rect(surface, (40, 46, 56), (bx, by, barw, 12),
                         border_radius=6)
        frac = max(0, self.time_left / ROUND_TIME)
        pygame.draw.rect(surface, config.WARN,
                         (bx, by, int(barw * frac), 12), border_radius=6)
        if matched:
            ui.text(surface, "HOLD IT...", area.centerx, by + 24, size=18,
                    color=config.OK, align="midtop")
        # progress pips
        for i in range(ROUNDS):
            c = config.OK if i < self.round else (60, 66, 76)
            pygame.draw.circle(surface, c,
                               (area.centerx - 30 + i * 30, by + 56), 8)
