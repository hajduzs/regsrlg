"""This module contains the Vec2 base class representing 2-dimensional vectors"""


class Vec2:
    """Simple class representing a 2d vector."""

    def __init__(self, x: float = 0, y: float = 0):
        self.x: float = x
        self.y: float = y

    def __getitem__(self, item: int):
        if item == 0:
            return self.x
        if item == 1:
            return self.y
        raise Exception(f'A vec2 can only be indexed by 0 (x) or 1 (y), not {item}')

    def __len__(self):
        return 2

    def __mul__(self, other):
        return self.__class__(self.x * other, self.y * other)

    def __truediv__(self, other):
        return self.__class__(self.x / other, self.y / other)

    def __add__(self, other):
        return self.__class__(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return self.__class__(self.x - other.x, self.y - other.y)

    def __str__(self):
        return f'Vec({self.x}; {self.y})'
