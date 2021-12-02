"""This simple class represents a point.
It is derived form Vec2."""

from src.geometry.Vec2 import Vec2


class Point(Vec2):

    # Ordering: first X coordinates, then Y. 

    def __eq__(self, other: object) -> bool:
        return self.x == other.x and self.y == other.y

    def __lt__(self, other: object) -> bool:
        return self.x < other.x or ( self.x == other.x and self.y < other.y )

    def __str__(self):
        return f'Point({self.x}; {self.y})'

    def tolist(self):
        return [self.x, self.y]
