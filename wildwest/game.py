import math
import pyglet
from pyglet.window import key


FPS = 60

from .vector import v
from .wild import World
from .scenegraph import Scenegraph, Camera, DebugGeometryNode, StaticImage

from .hud import HUD


class CameraController(object):
    def __init__(self, camera):
        self.camera = camera

    def track(self, obj):
        self.target = obj.pos + v(0, 120)

    def update(self, dt):
        self.camera.offset = self.target


class LaggyCameraController(CameraController):
    RATE = 0.8

    def update(self, dt):
        r = (1 - self.RATE) ** dt
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


WIDTH = 800
HEIGHT = 600


class Game(object):
    """Control the game.

    Sets up the world, delegates to different game states.
    """
    def __init__(self):
        self.window = pyglet.window.Window(width=WIDTH, height=HEIGHT)
        self.load()

        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        self.window.push_handlers(
            on_draw=self.draw
        )
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

        self.restart()

    def restart(self):
        self.world = World()
        self.world.spawn_player()
        self.camera = Camera(v(self.world.hero.pos) + v(0, 220) - v(WIDTH * 0.5, 0), WIDTH, HEIGHT)
        self.camera_controller = LissajousCameraController(self.camera)

        self.set_gamestate(IntroGameState(self, self.world))

    def load(self):
        HUD.load()

    def draw(self):
        self.gamestate.draw(self.camera)

    def set_gamestate(self, gs):
        self.gamestate = gs
        gs.start()

    def update(self, dt):
        self.gamestate.update(dt)

    def set_debug(self):
        self.world.scene.add(DebugGeometryNode(self.world.physics))


class GameState(object):
    def __init__(self, game, world):
        self.game = game
        self.world = world

    def draw(self, camera):
        self.world.scene.draw(camera)

    def start(self):
        pass

    def update(self, dt):
        pass


class IntroGameState(GameState):
    def start(self):
        pos = v(self.world.hero.pos)
        self.logo = StaticImage(pos + v(-670, 270), 'logo.png', 10)
        self.pressenter = StaticImage(pos + v(-580, -60), 'press-enter.png', 10)
        self.world.scene.add(self.logo)
        self.world.scene.add(self.pressenter)

    def update(self, dt):
        if self.game.keys[key.ENTER]:
            self.world.load_level('level1')
            self.world.scene.remove(self.pressenter)
            self.game.set_gamestate(PlayGameState(self.game, self.world))
        self.world.scene.update(dt)


class PlayGameState(GameState):
    def start(self):
        pyglet.clock.schedule_interval(self.update_ai, 0.5)
        self.world.hero.hero.set_handler('on_death', self.on_hero_death)

    def on_hero_death(self, char):
        print "We died!"
        pyglet.clock.schedule_once(self.end_game, 4)

    def process_input(self):
        self.world.process_input(self.game.keys)

    def end_game(self, dt):
        self.game.restart()

    def update(self, dt):
        dt = min(dt, 0.08)
        self.process_input()
        self.world.update(dt)

        if not getattr(self.world.hero, 'dead', False):
            self.game.camera_controller.track(self.world.hero)
        self.game.camera_controller.update(dt)
        self.world.scene.update(dt)

    def update_ai(self, dt):
        self.world.update_ai(dt)
