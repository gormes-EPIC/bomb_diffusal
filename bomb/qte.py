"""Quick-time events: a chance to claw back a mistake.

At random moments during play (only while the team is actually carrying a
mistake), the whole screen flashes a single colour with no instructions.  Player
2 has five seconds to press the button that colour *converts to* -- the same
colour translation Player 1 holds on the Simon decoder card.  Get it right and
one mistake is wiped off; miss it (wrong button, or the five seconds run out)
and nothing happens -- there is never a penalty.

This lives above the individual puzzles: it owns the whole screen and the button
input while it is firing, so the active puzzle is frozen for its short duration.
"""

from __future__ import annotations

import random

from . import audio, config, ui
from .puzzle_data import SIMON_RULES

WINDOW = 5.0            # seconds to respond
MIN_GAP = 20.0         # min seconds between events
MAX_GAP = 45.0         # max seconds between events
FEEDBACK_TIME = 1.6    # how long the "-1 MISTAKE" badge stays up after a win


def _play_positive():
    # Bright, cheerful two-note chord.
    audio.play(1047, 200, 0.4)      # C6
    audio.play(1319, 200, 0.4)      # E6


def _play_disappointed():
    # Low, downcast dyad.
    audio.play(196, 320, 0.4)       # G3
    audio.play(147, 320, 0.4)       # D3


class QuickTimeEvent:
    def __init__(self):
        self.active = False
        self.color = None          # the flashed colour key
        self.target_btn = None     # the button that colour converts to
        self.time_left = 0.0
        self.feedback_t = 0.0      # countdown for the post-win "-1" badge
        self._cooldown = random.uniform(MIN_GAP, MAX_GAP)

    def update(self, dt, inputs, game):
        if self.feedback_t > 0:
            self.feedback_t = max(0.0, self.feedback_t - dt)

        if self.active:
            self.time_left -= dt
            for c in inputs.button_down:
                if c == self.target_btn:            # correct conversion in time
                    game.mistakes = max(0, game.mistakes - 1)
                    _play_positive()                # positive noise
                    self.feedback_t = FEEDBACK_TIME  # show the "-1 MISTAKE" badge
                    self._end()
                else:                               # wrong button: disappointed
                    _play_disappointed()            # ...noise, but no visual
                    self._end()
                return
            if self.time_left <= 0:                 # timed out: nothing
                self._end()
            return

        # Idle: count down to the next event, but only bother firing one when
        # there is actually a mistake to remove.
        self._cooldown -= dt
        if self._cooldown <= 0:
            if game.mistakes > 0:
                self._fire()
            else:
                self._cooldown = random.uniform(MIN_GAP, MAX_GAP)

    def _fire(self):
        self.active = True
        self.color = random.choice(list(SIMON_RULES))
        # Every Simon rule maps to a single button colour (doubles repeat it).
        self.target_btn = SIMON_RULES[self.color][0]
        self.time_left = WINDOW

    def _end(self):
        self.active = False
        self.color = None
        self.target_btn = None
        self._cooldown = random.uniform(MIN_GAP, MAX_GAP)

    def draw(self, surface):
        """Fill the whole screen with the flashed colour -- no instructions."""
        if self.active:
            surface.fill(config.BTN_COLORS[self.color])

        # After a win, flash a big "-1 MISTAKE" in the top-right corner. Nothing
        # is drawn on a miss.
        if self.feedback_t > 0:
            x = config.SCREEN_WIDTH - 40
            ui.text(surface, "-1", x, 80, size=72, color=config.OK,
                    align="topright", bold=True)
            ui.text(surface, "MISTAKE", x, 156, size=26, color=config.OK,
                    align="topright", bold=True)
