"""Registry of the active puzzle modules.

Note: the Logic-Gates / "Turn on the LED" circuit puzzle still lives in
``logic_gates.py`` (and its data in ``puzzle_data.py``), but it is intentionally
left OUT of the rotation below, so it is neither randomly dealt nor documented.
Re-add ``LogicGates`` here to bring it back.
"""

from .prime_ops import PrimeOps
from .morse import Morse
from .simon import Simon
from .maze import Maze
from .navigation import Navigation
from .rhythm import Rhythm
from .glyph_addition import GlyphAddition
from .combination_lock import CombinationLock
from .scrambler import Scrambler
from .check_please import CheckPlease
from .secret_sketch import SecretSketch

# Order here is just the catalogue order.
ALL_PUZZLES = [
    PrimeOps,
    Morse,
    Simon,
    Maze,
    Navigation,
    Rhythm,
    GlyphAddition,
    CombinationLock,
    Scrambler,
    CheckPlease,
    SecretSketch,
]
