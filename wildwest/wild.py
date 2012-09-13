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
from geom import v, Rect, Segment

from physics import Body, StaticBody, Physics


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


class Player(object):
    MAX_WALK = 200  # limit on walk speed
    ACCEL = 120000  # acceleration when walking
    FRICTION = 1  # deceleration

    w = 32  # bounding box width
    h = 106  # bounding box height
    MASS = 100

    def __init__(self, world, pos, node):
        self.world = world
        self.node = node
        node.z = 1
        self.body = Body(Rect.from_cwh(v(0, self.h / 2), self.w, self.h), self.MASS, pos)
        self.world.physics.add_body(self.body)
        self.running = 0
        self.crouching = False
        self.shooting = False
        self.direction = RIGHT

    @property
    def pos(self):
        return self.body.pos

    @property
    def jumping(self):
        return not self.body.on_floor

    def jump(self):
        if not self.jumping:
            self.body.apply_impulse(v(0, 450))
            self.node.play('jumping')

    def left(self):
        if self.crouching:
            self.face_left()
            return
        self.running = -1
        self.body.apply_force(v(-self.ACCEL, 0))
        if not self.jumping:
            self.node.play('running')

    def right(self):
        if self.crouching:
            self.face_right()
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

    @property
    def hitlist(self):
        if self.crouching:
            off = v(self.direction * 69, 49)
        elif not self.jumping:
            off = v(self.direction * 58, 78)
        else:
            return []
        p1 = self.node.pos + off
        p2 = p1 + v(1000, random.uniform(-50, 50)) * self.direction
        seg = Segment(p1, p2)
        hit = self.world.physics.ray_query(seg)
        return hit

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
        seg = Segment(p1, p2)
        hit = self.world.physics.ray_query(seg)
        if hit:
            d = hit[0][0]
            if d <= 0:
                seg = None
            else:
                seg = seg.truncate(d)

        if seg:
            self.node.scenegraph.add(Bullet(seg))
        self.body.apply_impulse(v(-10, 0) * self.direction)
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
        self.node.pos = self.body.pos
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
            if abs(vx) < 50 and not self.running:
                self.body.v = v(0, self.body.v.y)
                self.node.play('standing')
            else:
                self.node.play('running')

        self.crouching = False
        self.running = 0
        return


class AI(object):
    MIN_DISTANCE = 700

    def __init__(self, world):
        self.world = world

    def update(self, dt):
        self.ai()

    def ai(self):
        hero = self.world.hero
        lawmen = [obj for obj in self.world.objects\
                    if isinstance(obj, Player) and\
                    obj is not self.world.hero
                ]

        for lawman in lawmen:
            # If hero is not in range, move towards him
            if random.random() < 0.5:
                self.defend(hero, lawman)
            else:
                self.attack(hero, lawman)

    def defend(self, hero, lawman):
        """A simple defensive strategy"""
        # locate the hero: distance, vector
        hero_pos = hero.pos
        hero_hitlist = hero.hitlist
        self_pos = lawman.pos
        distance = self_pos.distance_to(hero_pos)

        # Face the right direction
        if (self_pos - hero_pos).x > 0:
            # Hero is on the left
            lawman.face_left()
        else:
            # Hero is on the right
            lawman.face_right()

        # Defence: if direct line of shooting
        # 1. Crouch if hero is standing or jumping and preparing to shoot
        if hero.jumping:
            lawman.crouch()
        # 2. Jump if hero is crouching
        elif hero.crouching:
            lawman.jump()

    def attack(self, hero, lawman):
        """A simple attack strategy"""
        hero_pos = hero.pos
        # hero_hitlist = hero.hitlist
        self_pos = lawman.pos
        # distance = self_pos.distance_to(hero_pos)
        # Face the right direction
        if (self_pos - hero_pos).x > 0:
            # Hero is on the left
            lawman.face_left()
        else:
            # Hero is on the right
            lawman.face_right()

        # Attack:
        # 1. If hero is in direct range shoot
        # hitlist = lawman.hitlist
        lawman.shoot()

    def move(self, hero, lawman):
        # Motion:
        # 1. If an object is blocking, go past it
        # 2. Shoot and hide if hero is right in front
        return


class Crate(object):
    w = 74
    h = 77

    def __init__(self, world, pos):
        self.node = Animation('crate.json', pos)
        self.world = world
        self.body = Body(Rect.from_cwh(v(0, self.h / 2), self.w, self.h), 1000, pos, controller=self)
        self.world.physics.add_body(self.body)

    def update(self, dt):
        self.node.pos = self.body.pos


# class Lawman(StaticImage):
#     def __init__(self, pos):
#         StaticImage.__init__(self, pos, IMG_LAWMAN_STANDING)


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
        self.physics = Physics()

        # setup the scene
        self.physics.add_static(StaticBody([Rect.from_points((0, 0), (1024, 115))]))
        self.ai = AI(self)
        self.spawn_player()
        self.spawn_crate()
        self.spawn_lawman(v(600, 115))

    def spawn(self, obj):
        self.scene.add(obj.node)
        self.objects.append(obj)

    def spawn_crate(self, pos=v(400, 115)):
        crate = Crate(self, pos)
        self.scene.add(crate.node)
        self.objects.append(crate)

    def spawn_player(self):
        # all this should be done elsewhere
        start = v(90, 115)
        node = Animation('pc.json', start)
        # self.scene.add(node)
        self.hero = Player(self, start, node)
        self.spawn(self.hero)

    def spawn_lawman(self, pos):
        node = Animation('lawman.json', pos)
        lawman = Player(self, pos, node)
        self.spawn(lawman)

    def process_input(self, keys):
        if keys[KEY_DOWN]:
            self.hero.down()

        if keys[KEY_LEFT]:
            self.hero.left()
        elif keys[KEY_RIGHT]:
            self.hero.right()

        if keys[KEY_UP]:
            self.hero.jump()
        elif keys[KEY_SHOOT]:
            self.hero.shoot()

    def update(self, dt):
        self.physics.update(dt)

        for o in self.objects:
            o.update(dt)
        self.ai.update(dt)
