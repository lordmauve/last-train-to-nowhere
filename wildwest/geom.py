from collections import namedtuple
from vector import Vector, v


class Rect(namedtuple('BaseRect', 'l r b t')):
    """2D rectangle class."""    

    @classmethod
    def from_blwh(self, b, l, w, h):
        return Rect(
            l,
            l + w,
            b,
            b + h
        )


    @classmethod
    def from_points(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        if x2 < x1:
            x1, x2 = x2, x1

        if y2 < y1:
            y1, y2 = y2, y1

        return Rect(
            x1,
            x2,
            y1,
            y2
        )

    def contains(self, p):
        x, y = p
        return (
            self.l <= x < self.r and
            self.b <= y < self.t
        )

    @property
    def w(self):
        return self.r - self.l

    @property
    def h(self):
        return self.t - self.b

    def translate(self, off):
        x, y = off
        return Rect(
            self.l + x,
            self.r + x,
            self.b + y,
            self.t + y
        )
