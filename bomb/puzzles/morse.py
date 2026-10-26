"""Puzzle 2 -- Morse Code.

A word is blinked out on LED A in international Morse.  Player 2 watches the
blinks; Player 1 has the Morse card (manual), decodes, and types the word.
"""

from __future__ import annotations

import random

import pygame

from .. import audio, config, ui
from ..puzzle_data import MORSE, MORSE_WORDS
from .base import Puzzle

UNIT = 0.25         # seconds per Morse "dot" unit
BLINK_COLOR = (235, 235, 245)


def _timeline(word):
    """List of (duration_s, on_bool) for one play-through of the word."""
    tl = []
    for li, letter in enumerate(word):
        code = MORSE[letter]
        for si, sym in enumerate(code):
            tl.append(((1 if sym == "." else 3) * UNIT, True))
            tl.append((UNIT, False))              # intra-letter gap
        tl[-1] = (3 * UNIT, False)                # letter gap
    tl.append((7 * UNIT, False))                  # word gap before repeat
    return tl


class Morse(Puzzle):
    name = "MORSE CODE"
    blurb = "Decode the Morse blinking on LED A and type the word."

    def start(self):
        self.word = random.choice(MORSE_WORDS)
        self.timeline = _timeline(self.word)
        self.idx = 0
        self.t = 0.0
        self.typed = ""
        self.wrong = False
        self._set_led(self.timeline[0][1])

    def _set_led(self, on):
        self.hw.led_a.set_color(BLINK_COLOR if on else (0, 0, 0))

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

    def update(self, dt, inputs):
        self.t += dt
        dur, on = self.timeline[self.idx]
        if self.t >= dur:
            self.t -= dur
            was_on = on
            self.idx = (self.idx + 1) % len(self.timeline)
            now_on = self.timeline[self.idx][1]
            self._set_led(now_on)
            if now_on and not was_on:
                audio.play(620, 90, 0.25)

    def draw(self, surface, area):
        self.title(surface, area)
        ui.text(surface, "Player 2 reads the LED-A blinks. Type the word:",
                area.centerx, area.y + 56, size=18, color=config.GREY,
                align="midtop")
        # letter blanks
        n = len(self.word)
        slot = 60
        total = n * slot
        sx = area.centerx - total // 2
        y = area.centery
        for i in range(n):
            x = sx + i * slot + slot // 2
            pygame.draw.line(surface, config.LIGHT, (x - 22, y + 26),
                             (x + 22, y + 26), 3)
            ch = self.typed[i] if i < len(self.typed) else ""
            col = config.DANGER if self.wrong else config.WHITE
            ui.text(surface, ch, x, y, size=52, color=col, align="center", bold=True)
        if self.wrong:
            ui.text(surface, "Incorrect - backspace and retry.",
                    area.centerx, y + 80, size=18, color=config.DANGER,
                    align="midtop")
