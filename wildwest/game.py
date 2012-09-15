import math
import pyglet
from pyglet.window import key


FPS = 60

from .vector import v
from .wild import World
from .scenegraph import Scenegraph, Camera, DebugGeometryNode

from .hud import HUD


class CameraController(object):
    def __init__(self, camera):
        self.camera = camera

    def track(self, obj):
        self.target = obj.pos + v(0, 120)

    def update(self, dt):
        self.camera.offset = self.target


class LaggyCameraController(CameraController):
    RATE = 0.5

    def update(self, dt):
        r = (1 - self.RATE ** dt)
        self.camera.offset = (
            (1 - r) * self.target +
            r * v(self.camera.offset)
        )


class LissajousCameraController(LaggyCameraController):
    t = 0
    XSCALE = 5
    YSCALE = 5
    FREQ = 1.3

    def track(self, obj):
        self.target = obj.pos + v(0, 120) + v(
            self.XSCALE * math.sin(3 * self.t * self.FREQ),
            self.YSCALE * math.cos(2 * self.t * self.FREQ),
        )

    def update(self, dt):
        self.t += dt
        super(LissajousCameraController, self).update(dt)



class Game(object):
    """Control the game.

    Sets up the world, hands input to specific objects.
    """
    def __init__(self):
        WIDTH = 800
        HEIGHT = 600
        self.window = pyglet.window.Window(width=WIDTH, height=HEIGHT)
        self.load()

        self.world = World()

        self.objects = []
        self.camera = Camera((200.0, 200.0), WIDTH, HEIGHT)
        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        self.window.push_handlers(
            on_draw=self.draw
        )
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)
        pyglet.clock.schedule_interval(self.update_ai, 0.5)
        self.world.load_level('level1')

        self.camera_controller = LissajousCameraController(self.camera)

    def load(self):
        HUD.load()

    def draw(self):
        self.world.scene.draw(self.camera)

    def process_input(self):
        self.world.process_input(self.keys)

    def update(self, dt):
        self.process_input()
        self.world.update(dt)

        if not getattr(self.world.hero, 'dead', False):
            self.camera_controller.track(self.world.hero)
        self.camera_controller.update(dt)
        self.world.scene.update(dt)

    def update_ai(self, dt):
        self.world.update_ai(dt)

    def set_debug(self):
        self.world.scene.add(DebugGeometryNode(self.world.physics))
