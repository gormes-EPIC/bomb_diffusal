"""Registry of all nine puzzle modules."""

from .prime_ops import PrimeOps
from .morse import Morse
from .simon import Simon
from .maze import Maze
from .navigation import Navigation
from .logic_gates import LogicGates
from .rhythm import Rhythm
from .glyph_addition import GlyphAddition
from .rotation_lock import RotationLock

# Order here is just the catalogue order.
ALL_PUZZLES = [
    PrimeOps,
    Morse,
    Simon,
    Maze,
    Navigation,
    LogicGates,
    Rhythm,
    GlyphAddition,
    RotationLock,
]
