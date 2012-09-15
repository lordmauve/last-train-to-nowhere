import re

from .svg import load_level_data

from . import wild
from .ai import AI


CLASSES = {
    'locomotive': wild.LocomotiveObject,
    'light': wild.Light,
    'health': wild.Health,
    'goldbar': wild.GoldBar,
    'crate': wild.Crate,
    'table': wild.Table,
}

CARRIAGES = ['car', 'freightcar', 'mailcar']


class UnknownObject(Exception):
    """Don't know how to instantiate this object."""


def load_level(world, name):
    for name, rect in load_level_data(name):
        name = re.sub(r'-(interior|exterior|standing)$', '', name)
        pos = rect.points[0]

        if name in CARRIAGES:
            wild.Carriage(pos=pos, name=name).spawn(world)
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
