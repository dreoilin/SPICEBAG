from enum import Enum

class Modes(Enum):
    NORMAL = 0
    INSERT = 1
    SELECT = 2

MODESTRS = {
    Modes.NORMAL : "NORMAL",
    Modes.INSERT : "INSERT",
    Modes.SELECT : "SELECT"
}

MODEFMT = "--{}--"
