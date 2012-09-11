from geom import v


GRAVITY = 40


class Body(object):
    def __init__(self, rect, mass, pos=v(0, 0)):
        assert mass > 0
        self.pos = pos
        self.rect = rect
        self.mass = mass
        self.v = v(0, 0)
        self.on_floor = False
        self.reset_forces()

    def get_rect(self):
        return self.rect.translate(self.pos)

    def reset_forces(self):
        self.f = v(0, -GRAVITY * self.mass)

    def apply_force(self, f):
        self.f += f

    def apply_impulse(self, impulse):
        self.v += impulse

    def update(self, dt):
        if self.mass == 0:
            return
        u = self.v
        self.v += self.f / self.mass
        if not self.v.is_zero:
            self.on_floor = False
        self.pos += 0.5 * (u + self.v) * dt


class StaticBody(object):
    def __init__(self, rectangles, pos=v(0, 0)):
        self.pos = pos
        self.rectangles = rectangles


class Physics(object):
    def __init__(self):
        self.static_geometry = []
        self.static_objects = []
        self.dynamic = []

    def add_body(self, b):
        self.dynamic.append(b)

    def add_static(self, s):
        self.static_objects.append(s)
        geom = []
        for o in s.rectangles:
            r = o.translate(s.pos)
            self.static_geometry.append(r)
            geom.append(r)
        s._geom = geom

    def remove_static(self, s):
        self.static_objects.remove(s)
        for r in s._geom:
            self.static_geometry.remove(r)

    def collide_static(self, d):
        r = d.get_rect()
        for s in self.static_geometry:
            mtd = r.intersects(s)
            if mtd:
                d.pos += mtd
                x, y = d.v
                if mtd.y:
                    y = 0
                    if mtd.y > 0:
                        d.on_floor = True
                    # TODO: apply friction
                if mtd.x:
                    x = 0
                d.v = v(x, y)

    def collide_dynamic(self, a, b):
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

        # Move the objects so as not to intersect
        a.pos += frac * mtd
        b.pos -= (1 - frac) * mtd
        
    def collide_velocities(self, c):
        """Work out the new velocities of objects in a collision."""
        a, mtd, b = c
        ua = a.v
        ub = b.v
        ma = a.mass
        mb = b.mass
        tm = ma + mb  # total mass

        # Inelastic collision, see http://en.wikipedia.org/wiki/Inelastic_collision
        com = (ma * ua + mb * ub) / tm

        dv = ub - ua
        cor = 0.2

        dm = cor * mb * dv / tm
        a.v = dm + com
        b.v = -dm + com
        return True

    def do_collisions(self):
        for d in self.dynamic:
            self.collide_static(d)

        collisions = []
        for i, d in enumerate(self.dynamic):
            for d2 in self.dynamic[i + 1:]:
                c = self.collide_dynamic(d, d2)
                if c:
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

        self.do_collisions()

        for d in self.dynamic:
            d.reset_forces()

