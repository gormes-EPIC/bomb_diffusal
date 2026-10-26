"""Global configuration for the Bomb Diffusal game.

Everything that the game loop, the puzzles, the hardware layer and the manual
generator need to agree on lives here (or in ``puzzle_data.py``).  Keeping it in
one place is what lets the printed manuals and the running program stay in sync.
"""

# --------------------------------------------------------------------------- #
# Display
# --------------------------------------------------------------------------- #
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
FULLSCREEN = False          # set True for the kiosk build on the Pi
TITLE = "BOMB DIFFUSAL"

# When no real GPIO is present we draw a small panel showing what Player 2's
# hardware (LEDs / buttons / encoder) is doing, so the game is playable and
# demonstrable on a plain desktop.
SHOW_HARDWARE_PANEL = True
PANEL_WIDTH = 300           # width of that right-hand mock panel

# Play-field width (everything left of the hardware panel).
def play_width():
    return SCREEN_WIDTH - (PANEL_WIDTH if SHOW_HARDWARE_PANEL else 0)

# --------------------------------------------------------------------------- #
# Game rules
# --------------------------------------------------------------------------- #
TOTAL_TIME = 30 * 60        # 30 minute bomb timer, in seconds
PUZZLES_PER_GAME = 6        # choose 6 of the possible puzzles each game

# --------------------------------------------------------------------------- #
# Colours (RGB tuples)
# --------------------------------------------------------------------------- #
BLACK = (10, 12, 16)
DARK = (22, 26, 34)
PANEL_BG = (16, 18, 24)
GREY = (120, 128, 140)
LIGHT = (210, 216, 226)
WHITE = (245, 247, 250)
ACCENT = (0, 200, 160)
WARN = (235, 180, 40)
DANGER = (220, 60, 60)
OK = (70, 200, 120)

# The four player buttons / Simon colours.  Keys used everywhere as identifiers.
BTN_COLORS = {
    "red": (220, 60, 60),
    "yellow": (235, 200, 40),
    "green": (70, 200, 120),
    "blue": (70, 130, 230),
}
BTN_ORDER = ["red", "yellow", "green", "blue"]

# --------------------------------------------------------------------------- #
# GPIO pin map (BCM numbering) -- used by hardware.py on a real Pi and printed
# in the parts list / wiring guide.  Change here if you wire it differently.
# --------------------------------------------------------------------------- #
PINS = {
    # RGB LED A  (the "target" LED)
    "led_a": {"r": 17, "g": 27, "b": 22},
    # RGB LED B  (the "team" LED)
    "led_b": {"r": 5, "g": 6, "b": 13},
    # Four coloured push buttons (to GND, internal pull-ups)
    "btn_red": 16,
    "btn_yellow": 20,
    "btn_green": 21,
    "btn_blue": 26,
    # Rotary encoder
    "enc_clk": 23,
    "enc_dt": 24,
    "enc_sw": 25,
    # Passive buzzer / piezo (optional -- audio also goes to the 3.5mm jack)
    "buzzer": 12,
}

# Common-anode LEDs invert the PWM signal.  Set True if you buy common-anode
# RGB LEDs instead of common-cathode.
LED_COMMON_ANODE = False

# --------------------------------------------------------------------------- #
# Desktop test key-bindings (used only by the mock hardware layer)
# --------------------------------------------------------------------------- #
#   button red/yellow/green/blue -> keys r / y / g / b
#   rotary encoder               -> mouse wheel, or ',' (CCW) and '.' (CW)
MOCK_BUTTON_KEYS = {
    "red": "r",
    "yellow": "y",
    "green": "g",
    "blue": "b",
}
