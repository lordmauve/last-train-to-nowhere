import pyglet
from pyglet.window import key


FPS = 60

from .vector import v
from .wild import make_scene, World
from .scenegraph import Camera, DebugGeometryNode



class Game(object):
    """Control the game.

    Sets up the world, hands input to specific objects.
    """
    def __init__(self):
        WIDTH = 800
        HEIGHT = 600
        self.window = pyglet.window.Window(width=WIDTH, height=HEIGHT)
        self.scene = make_scene()
        self.world = World(self.scene)
        self.objects = []
        self.camera = Camera((200.0, 200.0), WIDTH, HEIGHT)
        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        self.window.push_handlers(
            on_draw=self.draw
        )
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

    def draw(self):
        self.scene.draw(self.camera)

    def process_input(self):
        self.world.process_input(self.keys)

    def update(self, dt):
        self.process_input()
        self.world.update(dt)

        self.camera.offset = self.world.hero.pos + v(0, 120)
        self.scene.update(dt)

    def set_debug(self):
        self.scene.add(DebugGeometryNode(self.world.physics))
