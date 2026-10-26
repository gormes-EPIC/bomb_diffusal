"""Common interface every puzzle (module) implements."""

from __future__ import annotations

import pygame

from .. import config, ui


class Puzzle:
    name = "Module"
    # One-line hint shown on the module's intro card.
    blurb = ""

    def __init__(self, game):
        self.game = game
        self.hw = game.hw
        self.solved = False

    # --- lifecycle ---------------------------------------------------------
    def start(self):
        """Called once when the module becomes active."""

    def stop(self):
        """Called when leaving the module; turn hardware off by default."""
        self.hw.all_leds_off()

    # --- input / update / draw --------------------------------------------
    def handle_event(self, event):
        """Player 1 pygame events (mouse + keyboard)."""

    def update(self, dt, inputs):
        """dt = seconds since last frame; inputs = result of hw.poll()."""

    def draw(self, surface, area: pygame.Rect):
        """Draw into ``area`` (the play field, below the timer bar)."""

    # --- helpers -----------------------------------------------------------
    def title(self, surface, area):
        ui.text(surface, self.name, area.centerx, area.y + 16,
                size=30, color=config.ACCENT, align="midtop", bold=True)
