"""This class combines our own code (Rect)
with some functionality lifted from retrogamelib.
"""

import math
from collections import namedtuple
from vector import Vector, v


class BasePolygon(object):
    def __iter__(self):
        return iter(self.points)

    def project_to_axis(self, axis):
        projected_points = [p.dot(axis) for p in self.points]
        return Projection(min(projected_points), max(projected_points))
  
    def intersects(self, other):
        edges = self.edges
        edges.extend(other.edges)
        
        projections = []
        for edge in edges:
            axis = edge.normalised().perpendicular()
            
            self_projection = self.project_to_axis(axis)
            other_projection = other.project_to_axis(axis)
            intersection1 = self_projection.intersection(other_projection)
            intersection2 = -other_projection.intersection(self_projection)
            if not intersection1:
                return False
                
            proj_vector1 = v(axis.x * intersection1, axis.y * intersection1)
            proj_vector2 = v(axis.x * intersection2, axis.y * intersection2)
            projections.append(proj_vector1)
            projections.append(proj_vector2)
        
        mtd = -self.find_mtd(projections)
        
        return mtd
    
    def collide(self, other):
        mtd = self.intersects(other)
        if mtd:
            self.pos += mtd
    
    def find_mtd(self, push_vectors):
        mtd = push_vectors[0]
        mind2 = push_vectors[0].dot(push_vectors[0])
        for vector in push_vectors[1:]:
            d2 = vector.dot(vector)
            if d2 < mind2:
                mind2 = d2
                mtd = vector
        return mtd


class Rect(BasePolygon, namedtuple('BaseRect', 'l r b t')):
    """2D rectangle class."""    

    @classmethod
    def from_blwh(cls, b, l, w, h):
        """From bottom left and dimensions"""
        return Rect(
            l,
            l + w,
            b,
            b + h
        )

    @classmethod
    def from_cwh(cls, c, w, h):
        """From center and dimensions"""
        w2 = w * 0.5
        h2 = h * 0.5
        return cls(
            c.x - w2,
            c.x + w2,
            c.y - h2,
            c.y + h2
        )

    @classmethod
    def from_points(cls, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        if x2 < x1:
            x1, x2 = x2, x1

        if y2 < y1:
            y1, y2 = y2, y1

        return cls(
            x1,
            x2,
            y1,
            y2
        )

    @property
    def points(self):
        return [
            v(self.l, self.b),
            v(self.l, self.t),
            v(self.r, self.t),
            v(self.r, self.b),
        ]

    @property
    def edges(self):
        edges = []
        points = self.points
        last = points[-1]
        for i, p in enumerate(points):
            edges.append(p - last)
            last = p
        return edges

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


 
class Projection(object):
    def __init__(self, min, max):
        self.min, self.max = min, max
   
    def intersection(self, other):
        if self.max > other.min and other.max > self.min:
            return self.max-other.min
        return 0
 

class ConvexPolygon(BasePolygon):
    def __init__(self, pos, points):
        if type(pos) in [type(()), type([])]:
            self.pos = v(pos)

        self.points = []
        for p in points:
            self.points.append(v(*p))
        
        self.edges = []
        for i in range(len(self.points)):
            point = self.points[i]
            next_point = self.points[(i + 1) % len(self.points)]
            self.edges.append(next_point - point)
