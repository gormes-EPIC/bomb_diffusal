"""Puzzle 2 -- Morse Code.

A word is blinked out on LED A in international Morse.  Player 2 watches the
blinks; Player 1 has the Morse card (manual), decodes, and types the word.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from ..puzzle_data import MORSE, MORSE_WORDS
from .base import Puzzle

UNIT = 0.4          # seconds per Morse "dot" unit
INTRA_GAP = 1       # * UNIT -- gap between symbols within a letter
LETTER_GAP = 6      # * UNIT -- gap between letters (long, so it's easy to read)
WORD_GAP = 9        # * UNIT -- gap before the word repeats
READY_ON = 2        # * UNIT -- length of each red "get ready" flash
READY_GAP = 1       # * UNIT -- gap between the red flashes

DOT_COLOR = (60, 220, 90)       # green: a dot (.)
DASH_COLOR = (70, 130, 240)     # blue: a dash (-)
READY_COLOR = (220, 60, 60)     # red: "a new word is starting"


def _timeline(word):
    """List of (duration_s, color_or_None) for one play-through of the word.

    ``color`` is the LED colour while on, or ``None`` for an off (gap) beat.
    """
    tl = []
    # Two red flashes announce that the word is about to start (and repeat).
    for _ in range(2):
        tl.append((READY_ON * UNIT, READY_COLOR))
        tl.append((READY_GAP * UNIT, None))
    tl.append((LETTER_GAP * UNIT, None))          # beat before the code begins

    for letter in word:
        code = MORSE[letter]
        for sym in code:
            if sym == ".":
                tl.append((1 * UNIT, DOT_COLOR))
            else:
                tl.append((4 * UNIT, DASH_COLOR))
            tl.append((INTRA_GAP * UNIT, None))   # intra-letter gap
        tl[-1] = (LETTER_GAP * UNIT, None)        # letter gap (overwrites last)
    tl[-1] = (WORD_GAP * UNIT, None)              # word gap before repeat
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

    def _set_led(self, color):
        self.hw.led_a.set_color(color if color else (0, 0, 0))

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
        self.t += dt
        dur = self.timeline[self.idx][0]
        if self.t >= dur:
            self.t -= dur
            self.idx = (self.idx + 1) % len(self.timeline)
            self._set_led(self.timeline[self.idx][1])

    def draw(self, surface, area):
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
