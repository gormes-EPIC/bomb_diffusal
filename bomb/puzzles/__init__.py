"""Registry of all ten puzzle modules."""

from .color_mixing import ColorMixing
from .morse import Morse
from .simon import Simon
from .maze import Maze
from .navigation import Navigation
from .logic_gates import LogicGates
from .rhythm import Rhythm
from .symbols_lock import SymbolsLock
from .glyph_addition import GlyphAddition
from .rotation_lock import RotationLock

# Order here is just the catalogue order (Puzzle 1..10 from the spec).
ALL_PUZZLES = [
    ColorMixing,
    Morse,
    Simon,
    Maze,
    Navigation,
    LogicGates,
    Rhythm,
    SymbolsLock,
    GlyphAddition,
    RotationLock,
]
