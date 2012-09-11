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
                if mtd.x:
                    x = 0
                d.v = v(x, y)

    def collide_dynamic(self, d, d2):
        pass  # TODO: resolve collision

    def _iterate(self):
        for d in self.dynamic:
            self.collide_static(d)

        for i, d in enumerate(self.dynamic):
            for d2 in self.dynamic[i + 1:]:
                self.collide_dynamic(d, d2)

    def solve_collisions(self):
        for i in xrange(5):
            if self._iterate():
                break

    def update(self, dt):
        for d in self.dynamic:
            d.update(dt)

        self.solve_collisions()

        for d in self.dynamic:
            d.reset_forces()

