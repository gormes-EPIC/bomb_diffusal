"""Puzzle 10 -- Wire Scrambler (Enigma-style).

A pile of jumbled coloured wires carries six input letters through two black
"junction boxes" to six output letters.  To read the secret word, the team
traces, for each letter of the shown signal, its wire from the input terminal,
through the two boxes, to an output terminal -- and reads off the output letter.

The wires on either side of a box are drawn on screen, but the wiring *inside*
each black box is hidden: only Player 2's manual shows how each box's numbered
left ports connect to its right ports.  So Player 1 traces a wire up to a box
and reads its port number; Player 2 looks the box up and says which port it
comes out of; Player 1 traces onward.  Neither can trace a full wire alone.

Player 1 types the recovered word.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from ..puzzle_data import (SCRAMBLE_BOXES, SCRAMBLE_N, SCRAMBLE_WORDS)
from .base import Puzzle

# Distinct, easy-to-follow wire colours (one per terminal row).
WIRE_COLORS = [
    (232, 76, 76), (236, 150, 48), (230, 205, 64),
    (76, 200, 112), (72, 176, 232), (176, 112, 232),
]


def _rand_perm(n):
    p = list(range(n))
    random.shuffle(p)
    return p


class Scrambler(Puzzle):
    name = "WIRE SCRAMBLER"
    blurb = "Trace each wire through the hidden junction boxes to read the word."

    def start(self):
        self.wrong = False
        self.typed = ""
        for _ in range(200):
            if self._build():
                return
        # Extremely unlikely fallback: a trivial consistent setup.
        self._build()

    def _build(self) -> bool:
        n = SCRAMBLE_N
        self.n = n
        self.word = random.choice(SCRAMBLE_WORDS)

        # Build the six-letter terminal alphabet: the word's distinct letters
        # plus decoys to fill the terminals.
        distinct = list(dict.fromkeys(self.word))
        pool = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in distinct]
        random.shuffle(pool)
        alphabet = distinct + pool[: n - len(distinct)]
        if len(alphabet) != n:
            return False

        # Terminal labels (independent shuffles for the two sides).
        self.in_letters = random.sample(alphabet, n)
        self.out_letters = random.sample(alphabet, n)

        # Two distinct hidden boxes and three visible wire permutations.
        self.box_names = random.sample(list(SCRAMBLE_BOXES), 2)
        self.rho1 = SCRAMBLE_BOXES[self.box_names[0]]
        self.rho2 = SCRAMBLE_BOXES[self.box_names[1]]
        self.permA = _rand_perm(n)   # input row     -> box1 left port
        self.permB = _rand_perm(n)   # box1 right port-> box2 left port
        self.permC = _rand_perm(n)   # box2 right port-> output row

        # Decoded letter reached from each input row.
        out_of_in = {}
        for i in range(n):
            p = self.permA[i]
            q = self.rho1[p]
            r = self.permB[q]
            s = self.rho2[r]
            j = self.permC[s]
            out_of_in[i] = self.out_letters[j]

        # The signal is the word, written in input letters: for each target
        # letter, the input terminal that decodes to it.
        letter_to_input = {out_of_in[i]: self.in_letters[i] for i in range(n)}
        if any(c not in letter_to_input for c in self.word):
            return False
        self.signal = [letter_to_input[c] for c in self.word]

        # Self-check: tracing the signal must reproduce the word.
        decode_for_input = {self.in_letters[i]: out_of_in[i] for i in range(n)}
        if "".join(decode_for_input[s] for s in self.signal) != self.word:
            return False

        self._layout()
        return True

    # ------------------------------------------------------------- geometry
    def _layout(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.col_in = a.left + 230
        self.b1l, self.b1r = a.left + 560, a.left + 690
        self.b2l, self.b2r = a.left + 1050, a.left + 1180
        self.col_out = a.right - 230
        top, bottom = a.y + 190, a.y + 190 + 112 * (self.n - 1)
        self.rows = [top + (bottom - top) * r / (self.n - 1)
                     for r in range(self.n)]
        self.cx = a.centerx

    # ---------------------------------------------------------------- input
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

    # ----------------------------------------------------------------- draw
    def draw(self, surface, area):
        self._draw_signal(surface, area)
        self._draw_wires(surface)
        self._draw_boxes(surface)
        self._draw_terminals(surface)
        self._draw_answer(surface, area)

    def _draw_signal(self, surface, area):
        # The sequence of input letters to trace, shown as tiles up top.
        tile, gap = 58, 12
        total = len(self.signal) * tile + (len(self.signal) - 1) * gap
        sx = self.cx - total // 2
        y = area.y + 30
        for i, ch in enumerate(self.signal):
            rect = pygame.Rect(sx + i * (tile + gap), y, tile, tile)
            pygame.draw.rect(surface, (26, 30, 38), rect, border_radius=8)
            pygame.draw.rect(surface, config.ACCENT, rect, 2, border_radius=8)
            ui.text(surface, ch, rect.centerx, rect.centery, size=34,
                    color=config.WHITE, align="center", bold=True)

    # -- wires: three bundles of smooth coloured curves ---------------------
    def _draw_wires(self, surface):
        # Bundle A: inputs -> box1 left ports.
        for i in range(self.n):
            self._wire(surface, self.col_in, self.rows[i],
                       self.b1l, self.rows[self.permA[i]], WIRE_COLORS[i])
        # Bundle B: box1 right ports -> box2 left ports.
        for q in range(self.n):
            self._wire(surface, self.b1r, self.rows[q],
                       self.b2l, self.rows[self.permB[q]], WIRE_COLORS[q])
        # Bundle C: box2 right ports -> outputs.
        for s in range(self.n):
            self._wire(surface, self.b2r, self.rows[s],
                       self.col_out, self.rows[self.permC[s]], WIRE_COLORS[s])

    @staticmethod
    def _wire(surface, x0, y0, x1, y1, color):
        # Cubic bezier with a little vertical weave so the bundle reads as a
        # jumbled pile rather than neat parallel lines.
        dx = x1 - x0
        weave = 26 if (int(y0 + y1) // 7) % 2 == 0 else -26
        c1 = (x0 + dx * 0.42, y0 + weave)
        c2 = (x1 - dx * 0.42, y1 - weave)
        pts = []
        steps = 26
        for k in range(steps + 1):
            t = k / steps
            u = 1 - t
            x = (u**3 * x0 + 3 * u*u*t * c1[0] + 3 * u*t*t * c2[0] + t**3 * x1)
            y = (u**3 * y0 + 3 * u*u*t * c1[1] + 3 * u*t*t * c2[1] + t**3 * y1)
            pts.append((x, y))
        ipts = [(int(x), int(y)) for x, y in pts]
        pygame.draw.lines(surface, (12, 14, 18), False, ipts, 8)   # shadow
        pygame.draw.lines(surface, color, False, ipts, 4)          # core

    # -- the two black junction boxes --------------------------------------
    def _draw_boxes(self, surface):
        self._box(surface, self.b1l, self.b1r, self.box_names[0])
        self._box(surface, self.b2l, self.b2r, self.box_names[1])

    def _box(self, surface, xl, xr, name):
        top = self.rows[0] - 46
        bot = self.rows[-1] + 46
        rect = pygame.Rect(xl, top, xr - xl, bot - top)
        pygame.draw.rect(surface, (6, 7, 10), rect, border_radius=10)
        pygame.draw.rect(surface, (70, 78, 92), rect, 3, border_radius=10)
        ui.text(surface, name, rect.centerx, rect.y - 6, size=30,
                color=config.LIGHT, align="midbottom", bold=True)
        # Numbered ports down each edge (1..N), the only clue to the hidden
        # wiring inside -- Player 2's manual maps left ports to right ports.
        for r in range(self.n):
            y = int(self.rows[r])
            for x, side in ((xl, "L"), (xr, "R")):
                pygame.draw.circle(surface, (210, 216, 226), (x, y), 9)
                pygame.draw.circle(surface, (40, 46, 56), (x, y), 9, 2)
                ui.text(surface, str(r + 1), x, y, size=14,
                        color=config.BLACK, align="center", bold=True)

    def _draw_terminals(self, surface):
        for i in range(self.n):
            y = int(self.rows[i])
            self._terminal(surface, self.col_in, y, self.in_letters[i],
                           WIRE_COLORS[i], left=True)
        for j in range(self.n):
            y = int(self.rows[j])
            # Output terminals are neutral -- their letter is the prize.
            self._terminal(surface, self.col_out, y, self.out_letters[j],
                           (150, 158, 172), left=False)

    @staticmethod
    def _terminal(surface, x, y, letter, color, left):
        pygame.draw.circle(surface, color, (x, y), 11)
        pygame.draw.circle(surface, config.BLACK, (x, y), 11, 2)
        lx = x - 30 if left else x + 30
        align = "midright" if left else "midleft"
        ui.text(surface, letter, lx, y, size=34, color=config.WHITE,
                align=align, bold=True)

    def _draw_answer(self, surface, area):
        n = len(self.word)
        slot = 56
        total = n * slot
        sx = self.cx - total // 2
        y = area.bottom - 90
        for i in range(n):
            x = sx + i * slot + slot // 2
            pygame.draw.line(surface, config.LIGHT, (x - 20, y + 24),
                             (x + 20, y + 24), 3)
            ch = self.typed[i] if i < len(self.typed) else ""
            col = config.DANGER if self.wrong else config.WHITE
            ui.text(surface, ch, x, y, size=46, color=col, align="center",
                    bold=True)
        if self.wrong:
            ui.text(surface, "Incorrect - backspace and retry.", self.cx,
                    y + 54, size=18, color=config.DANGER, align="midtop")
