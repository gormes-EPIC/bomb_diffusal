"""Puzzle 3 -- Simon with a Twist.

LED A flashes a colour sequence.  Player 1's decoder card translates each shown
colour into one or more *button* colours (e.g. green -> red, blue -> 2 yellows).
Player 2 presses the translated sequence on the four buttons.  A wrong press
resets the input.
"""

from __future__ import annotations

import random

from .. import audio, config, ui
from ..puzzle_data import BUTTON_TONE, SIMON_RULES, SIMON_SEQUENCE_LEN
from .base import Puzzle

FLASH_ON = 0.55
FLASH_GAP = 0.3
LOOP_GAP = 1.4


class Simon(Puzzle):
    name = "SIMON WITH A TWIST"
    blurb = "Decode the LED-A colour flashes with the card, press the buttons."

    def start(self):
        colors = list(SIMON_RULES.keys())
        self.sequence = [random.choice(colors) for _ in range(SIMON_SEQUENCE_LEN)]
        self.required = []
        for c in self.sequence:
            self.required.extend(SIMON_RULES[c])
        self.progress = 0
        self.wrong_flash = 0.0
        self.t = 0.0
        self.flash_idx = -1       # -1 == inter-loop gap
        self.hw.led_a.off()

    def _advance_flash(self):
        self.flash_idx += 1
        if self.flash_idx >= len(self.sequence):
            self.flash_idx = -1
            self.hw.led_a.off()
        else:
            self.hw.led_a.set_color(config.BTN_COLORS[self.sequence[self.flash_idx]])

    def update(self, dt, inputs):
        if self.wrong_flash > 0:
            self.wrong_flash = max(0, self.wrong_flash - dt)
        # animate LED A flashing
        self.t += dt
        if self.flash_idx == -1:
            if self.t >= LOOP_GAP:
                self.t = 0.0
                self._advance_flash()
        else:
            # on for FLASH_ON then gap FLASH_GAP (led off) handled below
            on_phase = self.t < FLASH_ON
            self.hw.led_a.set_color(
                config.BTN_COLORS[self.sequence[self.flash_idx]] if on_phase
                else (0, 0, 0))
            if self.t >= FLASH_ON + FLASH_GAP:
                self.t = 0.0
                self._advance_flash()

        # handle button presses
        for c in inputs.button_down:
            audio.play(BUTTON_TONE[c], 120, 0.3)
            if c == self.required[self.progress]:
                self.progress += 1
                if self.progress == len(self.required):
                    self.solved = True
            else:
                self.progress = 0
                self.wrong_flash = 0.5

    def draw(self, surface, area):
        # progress pips
        n = len(self.required)
        slot = 46
        sx = area.centerx - n * slot // 2
        y = area.centery
        for i in range(n):
            x = sx + i * slot + slot // 2
            if self.wrong_flash > 0:
                col = config.DANGER
            elif i < self.progress:
                col = config.OK
            else:
                col = (60, 66, 76)
            import pygame
            pygame.draw.circle(surface, col, (x, y), 16)
