import math
import pyglet
from pyglet.window import key


FPS = 60

from .vector import v
from .wild import World
from .scenegraph import Scenegraph, Camera, DebugGeometryNode, StaticImage, FadeyImage

from .hud import HUD


class CameraController(object):
    def __init__(self, camera):
        self.camera = camera

    def track(self, obj):
        self.target = obj.pos + v(0, 120)

    def update(self, dt):
        self.camera.offset = self.target


class LaggyCameraController(CameraController):
    RATE = 0.9

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
        pyglet.clock.schedule(self.update)

        self.restart()

    def debug_allocation(self, dt):
        import gc
        print "World objects:", len(self.world.objects)
        print "Physical objects:", len(self.world.physics.dynamic)
        print "Scenegraph nodes:", len(self.world.scene.objects)
        print "Garbage:", len(gc.garbage)

    def restart(self, gamestate=None):
        self.world = World()
        self.world.spawn_player()
        self.camera = Camera(v(self.world.hero.pos) + v(0, 220) - v(WIDTH * 0.5, 0), WIDTH, HEIGHT)
        self.camera_controller = LissajousCameraController(self.camera)

        if gamestate is None:
            gamestate = IntroGameState
        self.set_gamestate(gamestate(self, self.world))

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
        pyglet.clock.schedule_interval(self.debug_allocation, 1)


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
        self.logo = FadeyImage(pos + v(-670, 270), 'logo.png', 10)
        self.pressenter = StaticImage(pos + v(-580, -60), 'press-enter.png', 10)
        self.world.scene.add(self.logo)
        self.world.scene.add(self.pressenter)

    def update(self, dt):
        self.logo.show()
        if self.game.keys[key.ENTER]:
            self.world.scene.remove(self.pressenter)
            self.game.set_gamestate(PlayGameState(self.game, self.world))
        self.world.scene.update(dt)


class PlayGameState(GameState):
    level = 1

    def start(self):
        try:
            self.world.load_level('level%d' % self.level)
        except IOError:
            self.show_message(StaticImage((0, 0), 'the-end.png', 10), off=v(100, 220))
            PlayGameState.level = 1
            pyglet.clock.schedule_once(self.end_game, 10)


        self.welldone = StaticImage((0, 0), 'well-done.png', 10)
        self.welcome = StaticImage((0, 0), 'welcome.png', 10)

        pyglet.clock.schedule_interval(self.update_ai, 0.5)
        self.world.hero.hero.set_handler('on_death', self.on_hero_death)
        self.world.set_handler('on_goal', self.on_goal)

        self.won = False

    def __del__(self):
        pyglet.clock.unschedule(self.update_ai)

    def show_message(self, node, off=v(0, 100)):
        w = node.sprite.image.width
        node.pos = v(self.world.hero.pos) + v(-w * 0.5, 0) + off
        self.world.scene.add(node)

    def on_hero_death(self, char):
        self.show_message(self.welcome)
        pyglet.clock.schedule_once(self.end_game, 4)

    def on_goal(self, char):
        if not self.won:
            self.show_message(self.welldone, off=v(0, 200))
            pyglet.clock.schedule_once(self.next_level, 4)
            self.won = True

    def next_level(self, dt):
        PlayGameState.level += 1
        self.game.restart(PlayGameState)

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
