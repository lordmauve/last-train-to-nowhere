import pyglet
from pyglet.window import key


FPS = 60

from .vector import v
from .wild import World
from .scenegraph import Scenegraph, Camera, DebugGeometryNode



class Game(object):
    """Control the game.

    Sets up the world, hands input to specific objects.
    """
    def __init__(self):
        WIDTH = 800
        HEIGHT = 600
        self.window = pyglet.window.Window(width=WIDTH, height=HEIGHT)
        self.world = World()

        self.objects = []
        self.camera = Camera((200.0, 200.0), WIDTH, HEIGHT)
        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        self.window.push_handlers(
            on_draw=self.draw
        )
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

        self.world.load_level('level1')

    def draw(self):
        self.world.scene.draw(self.camera)

    def process_input(self):
        self.world.process_input(self.keys)

    def update(self, dt):
        self.process_input()
        self.world.update(dt)

        self.camera.offset = self.world.hero.pos + v(0, 120)
        self.world.scene.update(dt)

    def set_debug(self):
        self.world.scene.add(DebugGeometryNode(self.world.physics))
