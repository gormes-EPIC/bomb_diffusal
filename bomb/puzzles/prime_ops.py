"""Puzzle 1 -- Number Lock.

The lock starts on a random prime between 25 and 100 and shows a target value.
Each of the four buttons performs one of four operations -- x2, x3, -1, -3 --
assigned at random, with the mapping shown on screen.  Player 1 reads the
operations out; Player 2 presses buttons in an order that turns the starting
value into the target.

Every press that does not move the value one step closer to the target along a
shortest path counts as a mistake (and leaves the value unchanged), so the team
has to plan the chain rather than mash buttons.
"""

from __future__ import annotations

import random
from collections import deque

import pygame

from .. import audio, config, ui
from ..puzzle_data import BUTTON_TONE
from .base import Puzzle

# Primes in the inclusive range [25, 100].
PRIMES = [p for p in range(25, 101)
          if all(p % d for d in range(2, int(p ** 0.5) + 1))]

# The four operations, as (label, function).
OPS = [
    ("x2", lambda v: v * 2),
    ("x3", lambda v: v * 3),
    ("-1", lambda v: v - 1),
    ("-3", lambda v: v - 3),
]
_PRETTY = {"x2": "×2", "x3": "×3", "-1": "−1", "-3": "−3"}

CAP = 3000          # ceiling for the reachability search (shortest paths stay well below)
MAXVAL = 999        # keep generated targets to three digits
MIN_STEPS = 3       # shortest solution must take at least this many presses
MAX_STEPS = 6       # ...and at most this many


def _distance_map(target: int) -> dict[int, int]:
    """Shortest press-count from every value to ``target`` (BFS over inverses)."""
    dist = {target: 0}
    q = deque([target])
    while q:
        x = q.popleft()
        d = dist[x] + 1
        preds = [x + 1, x + 3]          # inverse of -1 and -3
        if x % 2 == 0:
            preds.append(x // 2)        # inverse of x2
        if x % 3 == 0:
            preds.append(x // 3)        # inverse of x3
        for y in preds:
            if 1 <= y <= CAP and y not in dist:
                dist[y] = d
                q.append(y)
    return dist


def _walk_target(start: int, steps: int) -> int:
    """Random forward walk from ``start`` to get a definitely-reachable target."""
    v = start
    for _ in range(steps):
        choices = [fn(v) for _, fn in OPS if 2 <= fn(v) <= MAXVAL]
        if not choices:
            break
        v = random.choice(choices)
    return v


class PrimeOps(Puzzle):
    name = "NUMBER LOCK"
    blurb = "Chain the button operations to turn the start value into the target."

    def start(self):
        self.hw.all_leds_off()
        self.wrong = 0.0
        for _ in range(1000):
            start = random.choice(PRIMES)
            target = _walk_target(start, random.randint(MIN_STEPS, MAX_STEPS))
            if target == start or not (2 <= target <= MAXVAL):
                continue
            dist = _distance_map(target)
            d0 = dist.get(start)
            if d0 is not None and MIN_STEPS <= d0 <= MAX_STEPS:
                break
        else:                                   # pathological fallback
            start = random.choice(PRIMES)
            target = start - 1
            dist = _distance_map(target)

        self.begin = start
        self.target = target
        self.value = start
        self.dist = dist
        # Randomly assign the four operations to the four buttons.
        self.mapping = dict(zip(config.BTN_ORDER, random.sample(OPS, len(OPS))))

    def update(self, dt, inputs):
        if self.wrong > 0:
            self.wrong = max(0.0, self.wrong - dt)

        for c in inputs.button_down:
            label, fn = self.mapping[c]
            cand = fn(self.value)
            if self.dist.get(cand) == self.dist[self.value] - 1:
                self.value = cand
                audio.play(BUTTON_TONE[c], 120, 0.3)
                if self.value == self.target:
                    self.solved = True
            else:
                self.wrong = 0.5
                audio.play(150, 160, 0.3)       # low error buzz
                self.strike()

    def draw(self, surface, area):
        cx = area.centerx
        wrong = self.wrong > 0
        reached = self.value == self.target

        ui.text(surface, f"START  {self.begin}", cx, area.y + 40, size=24,
                color=config.GREY, align="midtop")

        val_col = config.DANGER if wrong else (config.OK if reached
                                               else config.WHITE)
        ui.text(surface, str(self.value), cx, area.centery - 70, size=120,
                color=val_col, align="center", bold=True)

        ui.text(surface, f"TARGET  {self.target}", cx, area.centery + 20,
                size=40, color=config.OK if reached else config.ACCENT,
                align="midtop", bold=True)

        if wrong:
            ui.text(surface, "Wrong move - that press doesn't lead to the target.",
                    cx, area.centery + 76, size=18, color=config.DANGER,
                    align="midtop")

        self._draw_ops(surface, area)

    def _draw_ops(self, surface, area):
        n = len(config.BTN_ORDER)
        cw, chh, gap = 150, 92, 30
        total = n * cw + (n - 1) * gap
        sx = area.centerx - total // 2
        y = area.bottom - chh - 40
        for i, c in enumerate(config.BTN_ORDER):
            label, _ = self.mapping[c]
            rect = pygame.Rect(sx + i * (cw + gap), y, cw, chh)
            col = config.BTN_COLORS[c]
            pygame.draw.rect(surface, tuple(int(v * 0.30) for v in col), rect,
                             border_radius=10)
            pygame.draw.rect(surface, col, rect, 3, border_radius=10)
            ui.text(surface, c.upper(), rect.centerx, rect.y + 14, size=18,
                    color=col, align="midtop", bold=True)
            ui.text(surface, _PRETTY[label], rect.centerx, rect.centery + 16,
                    size=44, color=config.WHITE, align="center", bold=True)
