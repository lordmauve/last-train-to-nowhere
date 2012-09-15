from .geom import v, Vector

from .spatialhash import SpatialHash


GRAVITY = 1000

inf = float('inf')
NaN = float('NaN')

def is_nan(v):
    return v != v

def is_inf(v):
    return v == inf


class Body(object):
    on_collide = None

    def __init__(self, rect, mass, pos=v(0, 0), controller=None, groups=0x0001, mask=0x00ff):
        assert mass > 0
        self.pos = pos
        self.rect = rect
        self.mass = mass

        # Select what can collide with what
        self.groups = groups
        self.mask = mask

        self.controller = controller
        self.v = Vector((0, 0))
        self.on_floor = False
        self.reset_forces()

    def get_rect(self):
        return self.rect.translate(self.pos)

    def reset_forces(self):
        self.f = Vector((0, -GRAVITY * self.mass))

    def apply_force(self, f):
        self.f += f

    def apply_impulse(self, impulse):
        self.v += impulse

    def update(self, dt):
        if is_inf(self.mass):
            return

        u = self.v
        self.v += dt * self.f / self.mass

        self.v = Vector((self.v.x * 0.05 ** dt, self.v.y))

        self.on_floor = False

        self.pos += 0.5 * (u + self.v) * dt

    def set_collision_handler(self, handler):
        self.on_collide = handler


class FloatingBody(Body):
    """A dynamic body on which gravity does not apply."""
    def reset_forces(self):
        self.f = v(0, 0)


class StaticBody(object):
    def __init__(self, rectangles, pos=v(0, 0)):
        self.pos = pos
        self.rectangles = rectangles


class Physics(object):
    def __init__(self):
        self.static_geometry = []
        self.static_objects = []
        self.static_hash = SpatialHash()
        self.dynamic = []

    def add_body(self, b):
        self.dynamic.append(b)

    def remove_body(self, b):
        self.dynamic.remove(b)

    def add_static(self, s):
        self.static_objects.append(s)
        geom = []
        for o in s.rectangles:
            r = o.translate(s.pos)
            self.static_hash.add_rect(r, (r, s))
            self.static_geometry.append(r)
            geom.append(r)
        s._geom = geom

    def remove_static(self, s):
        self.static_objects.remove(s)
        for r in s._geom:
            self.static_geometry.remove(r)
            self.static_hash.remove_rect(r, (r, s))

    def ray_query(self, segment, mask=0xffff):
        intersections = []
        for o in self.static_geometry:
            d = segment.intersects(o)
            if d:
                intersections.append((d, o))

        for o in self.dynamic:
            if o.groups & mask:
                d = segment.intersects(o.get_rect())
                if d:
                    intersections.append((d, o.controller))
        intersections.sort()
        return intersections

    def collide_static(self, d):
        r = d.get_rect()
        col = self.static_hash.potential_intersection(r)
        for s, body in col:
            mtd = r.intersects(s)
            if mtd:
                d.pos += mtd
                x, y = d.v
                if mtd.y:
                    y = 0
                    if mtd.y > 0:
                        d.on_floor = True
                if mtd.x:
                    x = 0
                d.v = Vector((x, y))

    def collide_dynamic(self, a, b):
        if not (a.groups & b.mask or a.mask & b.groups):
            return

        mtd = a.get_rect().intersects(b.get_rect())
        if mtd:
            return (a, mtd, b)

    def resolve_collision(self, c):
        """Move the objects involved in a collision so as not to intersect."""
        a, mtd, b = c
        ma = a.mass
        mb = b.mass
        tm = ma + mb  # total mass
        frac = mb / tm

        if is_inf(a.mass):
            frac = 0
        elif is_inf(b.mass):
            frac = 1

        # Move the objects so as not to intersect
        a.pos += frac * mtd
        b.pos -= (1 - frac) * mtd

        if mtd.y > 0:
            a.on_floor = True
        else:
            b.on_floor = True

    def collide_velocities(self, c):
        """Work out the new velocities of objects in a collision."""
        a, mtd, b = c
        perp = mtd.perpendicular()
        ua = mtd.project(a.v)
        ub = mtd.project(b.v)
        ma = a.mass
        mb = b.mass
        tm = ma + mb  # total mass
    
        if is_inf(tm):
            a.v = a.v - ua
            b.v = b.v - ub
            return True

        # Inelastic collision, see http://en.wikipedia.org/wiki/Inelastic_collision
        com = (ma * ua + mb * ub) / tm

        dv = ub - ua
        cor = 0.2

        dm = cor * mb * dv / tm
        a.v = perp.project(a.v) + dm + com
        b.v = perp.project(b.v) - dm + com
        return True

    def call_collision_callback(self, a, b, dt):
        ch = a.on_collide
        if ch is not None:
            ch(b, dt)

    def do_collisions(self, dt):
        for d in self.dynamic:
            self.collide_static(d)

        collisions = []
        for i, d in enumerate(self.dynamic):
            for d2 in self.dynamic[i + 1:]:
                c = self.collide_dynamic(d, d2)
                if c:
                    a, mtd, b = c
                    self.call_collision_callback(a, b, dt)
                    self.call_collision_callback(b, a, dt)
                    self.collide_velocities(c)
                    collisions.append(c)

        for i in xrange(5):
            if not collisions:
                break
            colliding = set()
            for c in collisions:
                self.resolve_collision(c)
                colliding.add(c[0])
                colliding.add(c[2])

            for d in colliding:
                self.collide_static(d)

            collisions = []
            for d in colliding:
                for d2 in self.dynamic:
                    if d is not d2:
                        c = self.collide_dynamic(d, d2)
                        if c:
                            collisions.append(c)

    def update(self, dt):
        for d in self.dynamic:
            d.update(dt)

        self.do_collisions(dt)

        for d in self.dynamic:
            d.reset_forces()

