import re

from .svg import load_level_data
from .geom import Rect, v
from .physics import FloatingBody

from . import wild
from .ai import AI


CLASSES = {
    'locomotive': wild.LocomotiveObject,
    'light': wild.Light,
    'health': wild.Health,
    'goldbar': wild.GoldBar,
    'crate': wild.Crate,
    'table': wild.Table,
    'seats': wild.Seats,
    'mailsack': wild.MailSack,
}

CARRIAGES = ['car', 'freightcar', 'mailcar']


class UnknownObject(Exception):
    """Don't know how to instantiate this object."""


def load_level(world, name):
    max_x = 0
    for name, rect in load_level_data(name):
        name = re.sub(r'-(interior|exterior|standing)$', '', name)
        pos = rect.points[0]

        if name in CARRIAGES:
            wild.Carriage(pos=pos, name=name).spawn(world)
            max_x += pos.x + 2048
        elif name == 'lawman':
            lawman = wild.Lawman(pos)
            lawman.spawn(world)
            lawman.ai = AI(lawman)
        else:
            try:
                cls = CLASSES[name]
            except KeyError:
                raise UnknownObject("Unknown object %s" % name)
            cls(pos).spawn(world)

    floor = FloatingBody(Rect(
            -1000, max_x,
            -100, 0
        ),
        mass=float('inf'),
        groups=0x8000
    )

    def floor_hit(o, dt):
        """Send things left, fast"""
        try:
            die = o.controller.die
        except AttributeError:
            pass
        else:
            die()
        o.apply_impulse(v(-10000, 0) * dt)

    floor.on_collide = floor_hit
    world.physics.add_body(floor)
