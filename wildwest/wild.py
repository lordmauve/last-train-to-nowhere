import sys

sys.path.insert(0, '..')
# import retrogamelib
# from retrogamelib.constants import *
# from retrogamelib import geometry

import random

import pyglet
from pyglet.window import key

from scenegraph import StaticImage, Scenegraph, Fill, RailTrack, Animation
from scenegraph import SkyBox, GroundPlane, Wheels, Locomotive, Bullet
from scenegraph import DebugGeometryNode
from scenegraph import Camera
from geom import v, Rect

from physics import Body, StaticBody, Physics


# Image File Paths
ASSETS_BASE = 'assets/sprites'
IMG_PC_STANDING = 'pc-standing.png'
IMG_PC_CROUCHING = 'pc-crouching.png'
IMG_LAWMAN_STANDING = 'lawman-standing.png'
IMG_LAWMAN_CROUCHING = 'lawman-crouching.png'
IMG_TABLE = 'table.png'
IMG_CRATE = 'crate.png'
IMG_CARRIAGE = 'car-interior.png'


# Key Bindings
KEY_RIGHT = key.RIGHT
KEY_LEFT = key.LEFT
KEY_DOWN = key.DOWN
KEY_UP = key.UP
KEY_SHOOT = key.X

RIGHT = 1
LEFT = -1

FLOOR_Y = 115


physics = Physics()
physics.add_static(StaticBody([Rect.from_points((0, 0), (1024, 115))]))


class Player(object):
    MAX_WALK = 200  # limit on walk speed
    ACCEL = 120000  # acceleration when walking
    FRICTION = 1  # deceleration

    w = 32  # bounding box width
    h = 106  # bounding box height
    MASS = 100

    def __init__(self, pos, node):
        self.node = node
        self.body = Body(Rect.from_cwh(v(0, self.h / 2), self.w, self.h), self.MASS, pos)
        physics.add_body(self.body)
        self.running = 0
        self.crouching = False
        self.shooting = False
        self.direction = RIGHT

    @property
    def jumping(self):
        return not self.body.on_floor

    def jump(self):
        if not self.jumping:
            self.body.apply_impulse(v(0, 450))
            self.node.play('jumping')

    def left(self):
        if self.crouching:
            self.node.set_flip(True)
            return
        self.running = -1
        self.body.apply_force(v(-self.ACCEL, 0))
        if not self.jumping:
            self.node.play('running')

    def right(self):
        if self.crouching:
            self.node.set_flip(False)
            return
        self.running = 1
        self.body.apply_force(v(self.ACCEL, 0))
        if not self.jumping:
            self.node.play('running')

    def down(self):
        self.crouch()

    def crouch(self):
        self.running = 0
        self.crouching = True

    def shoot(self):
        if self.shooting:
            return
        if self.crouching:
            self.node.play('crouching-shooting')
            off = v(self.direction * 69, 49)
        elif not self.jumping:
            self.node.play('standing-shooting')
            off = v(self.direction * 58, 78)
        else:
            return

        p1 = self.node.pos + off
        p2 = p1 + v(1000, random.uniform(-50, 50)) * self.direction
        self.node.scenegraph.add(Bullet(p1, p2))
        self.body.apply_impulse(v(-30, 0) * self.direction)
        self.shooting = True
        pyglet.clock.schedule_once(self.shooting_finish, 0.5)

    def shooting_finish(self, dt):
        self.shooting = False

    def face_left(self):
        self.node.set_flip(True)
        self.direction = LEFT

    def face_right(self):
        self.node.set_flip(False)
        self.direction = RIGHT

    def update(self, dt):
        self.pos = self.node.pos = self.body.pos
        vx, vy = self.body.v

        if self.running:
            if vx > 10:
                self.face_right()
            elif vx < -10:
                self.face_left()
        if self.shooting:
            pass
        elif self.crouching:
            self.node.play('crouching')
        elif self.jumping:
            if vy < -300:
                self.node.play('falling')
            elif vy < -100:
                self.node.play('standing')
        else:
            if self.node.playing == 'couching':
                self.node.play('standing')

            if abs(vx) < 50 and not self.running:
                self.body.v = v(0, self.body.v.y)
                self.node.play('standing')

        self.crouching = False
        self.running = 0
        return


class Crate(object):
    w = 74
    h = 77

    def __init__(self, pos):
        self.node = Animation('crate.json', pos)
        self.body = Body(Rect.from_cwh(v(0, self.h / 2), self.w, self.h), 1000, pos)
        physics.add_body(self.body)

    def update(self, dt):
        self.node.pos = self.body.pos


class Table(StaticImage):
    def __init__(self, pos):
        StaticImage.__init__(self, pos, IMG_TABLE)

class Hero(Player):
    def __init__(self, pos):
        Player.__init__(self, pos, IMG_PC_STANDING)


class Lawman(StaticImage):
    def __init__(self, pos):
        StaticImage.__init__(self, pos, IMG_LAWMAN_STANDING)


class Carriage(StaticImage):
    def __init__(self, pos):
        StaticImage.__init__(self, pos, IMG_CARRIAGE)
        self.allow_fall_through = False


def make_scene():
    s = Scenegraph()
    s.add(Carriage((0, 53)))
#    s.add(Hero((90, 115)))
#    s.add(Lawman((600, 115)))
#    s.add(Table((300, 115)))
    s.add(RailTrack(pyglet.resource.texture('track.png')))
    s.add(Wheels((91, 0)))
    s.add(Wheels((992 - 236, 0)))
    s.add(Locomotive((1024, 0)))

    ground = GroundPlane(
        (218, 176, 127, 255),
        (194, 183, 164, 255),
    )
    s.add(ground)

    s.add(SkyBox(
        (129, 218, 255, 255),
        (49, 92, 142, 255)
    ))

    return s


class World(object):
    """Collection of all the objects and geometry in the world."""
    def __init__(self, scenegraph):
        self.objects = []
        self.scene = scenegraph
        self.physics = physics

    def spawn(self, obj):
        self.scene.add(obj.node)
        self.objects.append(obj)

    def spawn_crate(self, pos=v(400, 115)):
        crate = Crate(pos)
        self.scene.add(crate.node)
        self.objects.append(crate)

    def update(self, dt):
        self.physics.update(dt)

        for o in self.objects:
            o.update(dt)

FPS = 60


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
        self.spawn_player()
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)
        self.world.spawn_crate()
        self.world.spawn_crate(v(600, 115))

    def spawn_player(self):
        # all this should be done elsewhere
        start = v(90, 115)
        node = Animation('pc.json', start)
        self.scene.add(node)
        self.hero = Player(start, node)
        self.world.spawn(self.hero)

    def draw(self):
        self.scene.draw(self.camera)

    def process_input(self):
        if self.keys[KEY_DOWN]:
            self.hero.down()

        if self.keys[KEY_LEFT]:
            self.hero.left()
        elif self.keys[KEY_RIGHT]:
            self.hero.right()

        if self.keys[KEY_UP]:
            self.hero.jump()
        elif self.keys[KEY_SHOOT]:
            self.hero.shoot()

    def update(self, dt):
        self.process_input()
        self.world.update(dt)

        self.camera.offset = self.hero.pos + v(0, 120)
        self.scene.update(dt)


def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--debug', action='store_true', help='Debug collision geometries')
    options, args = parser.parse_args()

    g = Game()
    if options.debug:
        g.scene.add(DebugGeometryNode(physics))
    pyglet.app.run()


if __name__ == '__main__':
    main()
