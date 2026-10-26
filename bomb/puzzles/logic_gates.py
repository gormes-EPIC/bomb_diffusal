"""Puzzle 6 -- Turn on the LED.

A circuit of AND/OR/NOT/XOR gates is shown with the gate types hidden (numbered
boxes).  Player 2's manual says which numbered box is which gate.  Player 1
clicks the input switches until the output lamp lights.
"""

from __future__ import annotations

import itertools
import random

import pygame

from .. import config, ui
from ..puzzle_data import CIRCUITS, circuit_output, eval_circuit
from .base import Puzzle


class LogicGates(Puzzle):
    name = "TURN ON THE LED"
    blurb = "Toggle the input switches until the output lamp lights."

    def start(self):
        # Pick a circuit and a STARTING input combination whose output is 0, so
        # the lamp begins OFF (unsolved) and the team actually has to solve it.
        # Also guarantee the circuit is solvable (some combo gives output 1).
        for _ in range(50):
            self.circuit = random.choice(CIRCUITS)
            names = list(self.circuit["inputs"])
            combos = [dict(zip(names, c))
                      for c in itertools.product([0, 1], repeat=len(names))]
            off = [s for s in combos if not circuit_output(self.circuit, s)]
            on = [s for s in combos if circuit_output(self.circuit, s)]
            if off and on:
                self.state = dict(random.choice(off))
                break
        else:                       # fallback: every switch off
            self.state = {name: 0 for name in self.circuit["inputs"]}
        self._geom()

    def _geom(self):
        a = pygame.Rect(40, 120, config.play_width() - 80,
                        config.SCREEN_HEIGHT - 180)
        self.area = a
        self.pos = {}
        for name, (nx, ny) in self.circuit["inputs"].items():
            self.pos[name] = (a.x + nx * a.w, a.y + ny * a.h)
        for g in self.circuit["gates"]:
            gx, gy = g["pos"]
            self.pos[g["id"]] = (a.x + gx * a.w, a.y + gy * a.h)
        self.lamp = (a.right - 10, a.y + 0.5 * a.h)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name in self.circuit["inputs"]:
                if (pygame.Vector2(self.pos[name]) -
                        pygame.Vector2(event.pos)).length() < 30:
                    self.state[name] ^= 1

    def update(self, dt, inputs):
        if circuit_output(self.circuit, self.state):
            self.solved = True

    def draw(self, surface, area):
        # Keep only the circuit name so Player 2 can find it in the manual.
        ui.text(surface, f"CIRCUIT {self.circuit['id']}", area.centerx,
                area.y + 30, size=22, color=config.LIGHT, align="midtop", bold=True)
        vals = eval_circuit(self.circuit, self.state)

        def wire(a, b, on):
            pygame.draw.line(surface, config.OK if on else (70, 76, 86),
                             a, b, 4 if on else 2)

        # wires into gates
        for i, g in enumerate(self.circuit["gates"], 1):
            for ref in g["in"]:
                wire(self.pos[ref], self.pos[g["id"]], vals[ref])
        wire(self.pos[self.circuit["output"]], self.lamp,
             vals[self.circuit["output"]])

        # input switches
        for name in self.circuit["inputs"]:
            p = self.pos[name]
            on = self.state[name]
            pygame.draw.circle(surface, config.OK if on else (60, 66, 76),
                               p, 22)
            pygame.draw.circle(surface, config.WHITE, p, 22, 2)
            ui.text(surface, "1" if on else "0", p[0], p[1], size=22,
                    color=config.BLACK if on else config.LIGHT,
                    align="center", bold=True)
            ui.text(surface, name.upper(), p[0] - 34, p[1], size=16,
                    color=config.GREY, align="midright")

        # gate boxes (numbered, type hidden)
        for i, g in enumerate(self.circuit["gates"], 1):
            p = self.pos[g["id"]]
            rect = pygame.Rect(0, 0, 70, 50)
            rect.center = p
            on = vals[g["id"]]
            pygame.draw.rect(surface, (34, 60, 48) if on else (44, 50, 60),
                             rect, border_radius=6)
            pygame.draw.rect(surface, config.OK if on else config.GREY,
                             rect, 2, border_radius=6)
            ui.text(surface, str(i), p[0], p[1], size=26, color=config.WHITE,
                    align="center", bold=True)

        # output lamp
        out = vals[self.circuit["output"]]
        ui.draw_led(surface, self.lamp, 26,
                    (255, 220, 70) if out else (50, 50, 40), "OUTPUT")
