"""Common interface every puzzle (module) implements."""

from __future__ import annotations

import pygame


class Puzzle:
    name = "Module"
    # One-line hint shown on the module's intro card.
    blurb = ""

    def __init__(self, game):
        self.game = game
        self.hw = game.hw
        self.solved = False

    # --- shared helpers ----------------------------------------------------
    def strike(self):
        """Register one incorrect input.

        The game counts these across every module; ``config.MAX_MISTAKES`` of
        them and the bomb explodes.  Harnesses without a mistake counter (the
        hardware bench test) simply ignore it, so a wrong press is never fatal
        there.
        """
        add = getattr(self.game, "add_mistake", None)
        if callable(add):
            add()

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
        """Draw into ``area`` (the play field, below the timer bar).

        Note: puzzles deliberately do NOT draw their name or any how-to text --
        working out what each module is and how it works is part of the game.
        """
