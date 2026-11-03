"""Puzzle 12 -- Line Clear (Tetris).

A single bar-piece falls slowly into a well whose bottom three rows are complete
except for one empty column -- a three-deep notch.  Player 1 slides the piece
left/right with the arrow keys; Player 2 spins it upright with the rotary
encoder.  Stand it vertically over the notch and let it drop to fill the gap and
clear all three lines at once.

A misplaced drop costs nothing: the well simply resets and a fresh piece spawns.
Only the bomb clock is against you -- and ``FALL_INTERVAL`` below makes the fall
as slow (or fast) as you like.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from .base import Puzzle

# --------------------------------------------------------------------------- #
# Tuning -- FALL_INTERVAL is the one knob for difficulty: seconds the piece
# takes to drop one row.  Larger = slower/easier.
# --------------------------------------------------------------------------- #
FALL_INTERVAL = 0.6
SOFT_DROP_INTERVAL = 0.05      # while Player 1 holds Down
WELL_W = 8
WELL_H = 14
GAP_DEPTH = 3                  # rows pre-filled (minus the notch) == lines to clear
GOAL_LINES = 3

CELL = 48
STACK_COL = (96, 106, 126)
PIECE_COL = (80, 205, 235)     # classic I-piece cyan
GHOST_COL = (80, 205, 235, 70)

# The bar piece in its two orientations, as (dx, dy) offsets from the pivot.
SHAPES = {
    0: [(-1, 0), (0, 0), (1, 0), (2, 0)],   # horizontal
    1: [(0, -1), (0, 0), (0, 1), (0, 2)],   # vertical
}


class Tetris(Puzzle):
    name = "LINE CLEAR"
    blurb = "Spin the bar upright over the gap and drop it to clear three lines."

    def start(self):
        self.gap_col = random.randrange(WELL_W)
        self.cleared = 0
        self.fall_t = 0.0
        self.soft = False
        self._reset_well()
        self._spawn()
        self._layout()

    def _reset_well(self):
        # Empty grid, then fill the bottom GAP_DEPTH rows except the notch column.
        self.grid = [[None] * WELL_W for _ in range(WELL_H)]
        for y in range(WELL_H - GAP_DEPTH, WELL_H):
            for x in range(WELL_W):
                if x != self.gap_col:
                    self.grid[y][x] = STACK_COL

    def _spawn(self):
        self.rot = 0                       # spawn horizontal, so it must be spun
        self.px = WELL_W // 2
        self.py = 1
        self.fall_t = 0.0
        if not self._valid(self.px, self.py, self.rot):
            self._reset_well()             # pathological: clear and try again

    def _layout(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.bx = a.centerx - WELL_W * CELL // 2
        self.by = a.y + 100
        self.cx = a.centerx

    # ---------------------------------------------------------------- helpers
    def _cells(self, px, py, rot):
        return [(px + dx, py + dy) for dx, dy in SHAPES[rot]]

    def _valid(self, px, py, rot):
        for x, y in self._cells(px, py, rot):
            if x < 0 or x >= WELL_W or y < 0 or y >= WELL_H:
                return False
            if self.grid[y][x] is not None:
                return False
        return True

    def _drop_y(self):
        """Row offset where the current piece would land (for the ghost)."""
        y = self.py
        while self._valid(self.px, y + 1, self.rot):
            y += 1
        return y

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and self._valid(self.px - 1, self.py, self.rot):
                self.px -= 1
            elif event.key == pygame.K_RIGHT and self._valid(self.px + 1, self.py, self.rot):
                self.px += 1
            elif event.key == pygame.K_DOWN:
                self.soft = True
        elif event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
            self.soft = False

    def update(self, dt, inputs):
        if self.solved:
            return

        # Player 2 spins the piece with the encoder (with a small wall-kick).
        if inputs.encoder_delta:
            new_rot = (self.rot + inputs.encoder_delta) % 2
            for dx in (0, -1, 1, -2, 2):
                if self._valid(self.px + dx, self.py, new_rot):
                    self.px += dx
                    self.rot = new_rot
                    break

        self.fall_t += dt
        interval = SOFT_DROP_INTERVAL if self.soft else FALL_INTERVAL
        if self.fall_t >= interval:
            self.fall_t = 0.0
            if self._valid(self.px, self.py + 1, self.rot):
                self.py += 1
            else:
                self._lock()

    def _lock(self):
        for x, y in self._cells(self.px, self.py, self.rot):
            self.grid[y][x] = PIECE_COL
        lines = self._clear_lines()
        if lines >= GOAL_LINES:
            self.cleared = lines
            self.solved = True
        else:
            # A misdrop: reset the well and hand them a fresh piece. No penalty.
            self._reset_well()
            self._spawn()

    def _clear_lines(self) -> int:
        kept = [row for row in self.grid if any(c is None for c in row)]
        cleared = WELL_H - len(kept)
        self.grid = [[None] * WELL_W for _ in range(cleared)] + kept
        return cleared

    # ------------------------------------------------------------------- draw
    def draw(self, surface, area):
        ui.text(surface, f"LINES  {min(self.cleared, GOAL_LINES)} / {GOAL_LINES}",
                self.cx, area.y + 26, size=34, color=config.ACCENT,
                align="midtop", bold=True)

        well = pygame.Rect(self.bx - 4, self.by - 4,
                           WELL_W * CELL + 8, WELL_H * CELL + 8)
        pygame.draw.rect(surface, (18, 22, 30), well, border_radius=6)
        pygame.draw.rect(surface, (60, 68, 82), well, 3, border_radius=6)

        # grid + stack
        for y in range(WELL_H):
            for x in range(WELL_W):
                self._cell(surface, x, y, self.grid[y][x])

        # ghost (where it will land) then the live piece
        gy = self._drop_y()
        for x, y in self._cells(self.px, gy, self.rot):
            self._ghost(surface, x, y)
        for x, y in self._cells(self.px, self.py, self.rot):
            self._cell(surface, x, y, PIECE_COL)

        ui.text(surface, "P1:  ←  →  move        P2:  spin to rotate",
                self.cx, well.bottom + 18, size=20, color=config.GREY,
                align="midtop")

    def _cell(self, surface, x, y, color):
        rect = pygame.Rect(self.bx + x * CELL, self.by + y * CELL, CELL, CELL)
        if color is None:
            pygame.draw.rect(surface, (26, 30, 40), rect)
            pygame.draw.rect(surface, (34, 40, 52), rect, 1)
        else:
            inner = rect.inflate(-4, -4)
            pygame.draw.rect(surface, color, inner, border_radius=4)
            pygame.draw.rect(surface, tuple(min(255, c + 40) for c in color[:3]),
                             inner, 2, border_radius=4)

    def _ghost(self, surface, x, y):
        rect = pygame.Rect(self.bx + x * CELL, self.by + y * CELL, CELL, CELL)
        g = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        g.fill((0, 0, 0, 0))
        pygame.draw.rect(g, GHOST_COL, g.get_rect().inflate(-4, -4), border_radius=4)
        surface.blit(g, rect)
