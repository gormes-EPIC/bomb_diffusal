"""Puzzle 4 -- Invisible Maze.

Player 1 sees only a dot and the goal; the walls are invisible.  Player 2 has
the numbered maze in the manual and calls out the moves.  Arrow keys move the
dot; walls block movement.  Reach the goal to solve.
"""

from __future__ import annotations

import random

import pygame

from .. import config, ui
from ..puzzle_data import get_maze, maze_count
from .base import Puzzle

_KEYDIR = {
    pygame.K_UP: ("N", (0, -1)),
    pygame.K_DOWN: ("S", (0, 1)),
    pygame.K_LEFT: ("W", (-1, 0)),
    pygame.K_RIGHT: ("E", (1, 0)),
}


class Maze(Puzzle):
    name = "INVISIBLE MAZE"
    blurb = "Navigate the hidden maze; Player 2 reads it from the manual."

    def start(self):
        self.index = random.randrange(maze_count())
        self.maze = get_maze(self.index)
        self.pos = list(self.maze["start"])
        self.bump = 0.0
        self._geom()

    def _geom(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.cell = 70
        gw = self.maze["w"] * self.cell
        gh = self.maze["h"] * self.cell
        self.ox = a.centerx - gw // 2
        self.oy = a.centery - gh // 2 + 20

    def _cell_center(self, cx, cy):
        return (self.ox + cx * self.cell + self.cell // 2,
                self.oy + cy * self.cell + self.cell // 2)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or event.key not in _KEYDIR:
            return
        d, (dx, dy) = _KEYDIR[event.key]
        cx, cy = self.pos
        if d in self.maze["cells"][cy][cx]:
            self.pos = [cx + dx, cy + dy]
            if tuple(self.pos) == self.maze["goal"]:
                self.solved = True
        else:
            self.bump = 0.25     # flash to show a wall was hit

    def update(self, dt, inputs):
        if self.bump > 0:
            self.bump = max(0, self.bump - dt)

    def draw(self, surface, area):
        self.title(surface, area)
        ui.text(surface, f"MAZE {self.index + 1}  -  use the arrow keys.",
                area.centerx, area.y + 56, size=18, color=config.GREY,
                align="midtop")
        # Grid of cell markers (NOT the walls -- those are invisible).
        for y in range(self.maze["h"]):
            for x in range(self.maze["w"]):
                c = self._cell_center(x, y)
                pygame.draw.circle(surface, (44, 50, 60), c, 3)
        # Goal
        gx, gy = self._cell_center(*self.maze["goal"])
        pygame.draw.rect(surface, config.OK, (gx - 16, gy - 16, 32, 32),
                         border_radius=4)
        ui.text(surface, "GOAL", gx, gy - 30, size=13, color=config.OK,
                align="midbottom")
        # Player dot
        px, py = self._cell_center(*self.pos)
        col = config.DANGER if self.bump > 0 else (235, 90, 90)
        pygame.draw.circle(surface, col, (px, py), 14)
        pygame.draw.circle(surface, config.WHITE, (px, py), 14, 2)
