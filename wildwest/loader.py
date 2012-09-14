import re

from .svg import load_level_data

from .wild import LocomotiveObject, Carriage, Crate, Player, Lawman, Health, GoldBar
from .ai import AI
from .scenegraph import Animation


def load_level(world, name):
    for name, rect in load_level_data(name):
        name = re.sub(r'-(interior|exterior|standing)$', '', name)
        pos = rect.points[0]

        if name == 'locomotive':
            LocomotiveObject(pos).spawn(world)
        elif name in ['car', 'freightcar', 'mailcar']:
            Carriage(pos=pos, name=name).spawn(world)
        elif name == 'crate':
            Crate(pos).spawn(world)
        elif name == 'lawman':
            lawman = Lawman(pos)
            lawman.spawn(world)
            lawman.ai = AI(lawman)
        elif name == 'table':
            pass
        elif name == 'goldbar':
            GoldBar(pos).spawn(world)
        elif name == 'health':
            Health(pos).spawn(world)
        else:
            raise ValueError("Unknown object %s" % name)


def spawn_lawman(world, pos):
    node = Animation('lawman.json', pos)
    lawman = Player(world, pos, node)
    lawman.ai = AI(lawman)
    world.spawn(lawman)
