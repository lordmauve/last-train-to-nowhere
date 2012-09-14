import sys

sys.path.insert(0, '..')
# import retrogamelib
# from retrogamelib.constants import *
# from retrogamelib import geometry

import random

import pyglet
from pyglet.window import key


from .scenegraph import Scenegraph, Animation, AnimatedEffect
from .scenegraph import SkyBox, GroundPlane, Bullet
from .scenegraph.railroad import Locomotive, RailTrack, CarriageInterior, CarriageExterior

from .svg import load_geometry
from geom import v, Rect, Segment

from physics import Body, StaticBody, Physics


# Key Bindings
KEY_RIGHT = key.RIGHT
KEY_LEFT = key.LEFT
KEY_DOWN = key.DOWN
KEY_UP = key.UP
KEY_SHOOT = key.X


RIGHT = 1
LEFT = -1

FLOOR_Y = 115

# Collision groups
GROUP_ALL = MASK_ALL = 0xffff
GROUP_PLAYER = 0x0001
GROUP_ENEMY = 0x0002
GROUP_SCENERY = 0x0004


class Player(object):
    MAX_WALK = 200  # limit on walk speed
    ACCEL = 120000  # acceleration when walking
    FRICTION = 1  # deceleration

    w = 32  # bounding box width
    h = 106  # bounding box height
    h_crouching = 70
    MASS = 100

    MAX_HEALTH = 100

    groups = GROUP_ALL  # collision groups
    attack = MASK_ALL  # objects we can attack

    def __init__(self, pos, node):
        self.node = node
        node.z = 1
        self.body = Body(Rect.from_cwh(v(0, self.h / 2), self.w, self.h), self.MASS, pos, controller=self, groups=self.groups)
        self.running = 0
        self.crouching = False
        self.shooting = False
        self.hit = False
        self.dead = False
        self.direction = RIGHT

        self.health = self.MAX_HEALTH

    def spawn(self, world):
        self.world = world
        world.objects.append(self)
        world.scene.add(self.node)
        world.physics.add_body(self.body)

    def kill(self, world):
        world.objects.remove(self)
        world.scene.remove(self.node)
        world.physics.remove_body(self.body)

    def die(self):
        self.dead = True
        self.node.play('dead')
        self.world.objects.remove(self)
        self.world.physics.remove_body(self.body)

    @property
    def pos(self):
        return self.body.pos

    @property
    def jumping(self):
        return not self.body.on_floor

    def on_hit(self, pos, vel):
        flip = v(1, 0).dot(vel) > 0
        blood = AnimatedEffect('bloodspray.json', pos, 1.1)
        blood.set_flip(flip)
        self.world.scene.add(blood)

        self.health -= random.uniform(10, 20)
        if self.health <= 0:
            self.die()
        else:
            self.node.play('hit')
            self.hit = True
            pyglet.clock.schedule_once(self.hit_finish, 0.3)

    def hit_finish(self, dt):
        """Called by a time to cancel the shooting animation."""
        self.hit = False

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
        if not self.crouching:
            self.body.rect = Rect.from_cwh(v(0, self.h_crouching / 2), self.w, self.h_crouching)
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

        p = self.node.pos + off
        self.world.shoot(p, self.direction, mask=self.attack)

        self.body.apply_impulse(v(-10, 0) * self.direction)
        self.shooting = True
        pyglet.clock.schedule_once(self.shooting_finish, 0.5)

    def shooting_finish(self, dt):
        """Called by a time to cancel the shooting animation."""
        self.shooting = False

    def face_left(self):
        """Have the character face left."""
        self.node.set_flip(True)
        self.direction = LEFT

    def face_right(self):
        """Have the character face right."""
        self.node.set_flip(False)
        self.direction = RIGHT

    def update(self, dt):
        """Update the character.

        Since the physics gives us a position we don't need to do much more to
        calculate it here. However we do need to cue up the right animations
        based on what has happened in the physics, plus any input.

        """
        
        self.node.pos = self.body.pos
        if self.dead:
            return

        vx, vy = self.body.v

        if self.running:
            if vx > 10:
                self.face_right()
            elif vx < -10:
                self.face_left()
        if self.hit:
            return
        elif self.crouching:
            self.node.play('crouching')
        elif self.shooting:
            pass
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

        if not self.crouching:
            self.body.rect = Rect.from_cwh(v(0, self.h / 2), self.w, self.h)
        self.crouching = False
        self.running = 0


class Lawman(Player):
    groups = GROUP_ENEMY     # collision groups
    attack = MASK_ALL & ~GROUP_ENEMY  # objects we can attack

    MAX_HEALTH = 40

    def __init__(self, pos):
        node = Animation('lawman.json', pos)
        super(Lawman, self).__init__(pos, node)


class Outlaw(Player):
    groups = GROUP_PLAYER     # collision groups
    attack = MASK_ALL & ~GROUP_PLAYER

    def __init__(self, pos):
        node = Animation('pc.json', pos)
        super(Outlaw, self).__init__(pos, node)


class Crate(object):
    w = 74
    h = 77

    def __init__(self, pos):
        self.node = Animation('crate.json', pos)
        self.body = Body(Rect.from_cwh(v(0, self.h / 2), self.w, self.h), 1000, pos, controller=self, groups=GROUP_SCENERY)

    def spawn(self, world):
        world.physics.add_body(self.body)
        world.scene.add(self.node)
        world.objects.append(self)

    def update(self, dt):
        self.node.pos = self.body.pos


class Carriage(object):
    """Utility for linking a carriage interior and exterior"""

    WIDTH = 1024

    def __init__(self, pos, name):
        pos = v(1, 0).project(pos)
        self.interior = CarriageInterior(pos, name)
        self.exterior = CarriageExterior(pos, name)
        self.body = StaticBody(load_geometry(name), v(0, 53) + pos)

        self.target_opacity = None
        self.opacity = 1

    def set_opacity(self, opacity):
        self.opacity = opacity
        self.exterior.set_opacity(opacity)

    def get_pos(self):
        return self.interior.pos

    def set_pos(self, pos):
        self.interior.pos = pos
        self.body.pos = v(0, 53) + pos
        self.exterior.pos = pos

    pos = property(get_pos, set_pos)

    def spawn(self, world):
        world.physics.add_static(self.body)
        world.scene.add(self.interior)
        world.scene.add(self.exterior)
        world.carriages.append(self)

    def remove(self, scenegraph):
        scenegraph.remove(self.interior)
        scenegraph.remove(self.exterior)

    def intersects(self, rect):
        l = self.pos.x
        r = l + self.WIDTH
        return rect.l < r and rect.r > l

    def set_show_interior(self, show):
        opacity = not show
        if self.target_opacity is None:
            self.set_opacity(opacity)
        self.target_opacity = opacity

    def update(self, dt):
        if self.target_opacity is None:
            return

        if self.target_opacity != self.opacity:
            new = 0.5 * self.target_opacity + 0.5 * self.opacity
            if abs(self.target_opacity - new) < 0.001:
                new = self.target_opacity
            self.set_opacity(new)


class LocomotiveObject(object):
    def __init__(self, pos):
        pos = v(1, 0).project(pos)
        self.node = Locomotive(pos)
        self.body = StaticBody(load_geometry('locomotive'), pos)

    def spawn(self, world):
        world.scene.add(self.node)
        world.physics.add_static(self.body)


class World(object):
    """Collection of all the objects and geometry in the world."""
    def __init__(self):
        self.objects = []
        self.carriages = []

        self.physics = Physics()

        self.scene = Scenegraph()
        self.make_scene()
        self.spawn_player()

    def load_level(self, name):
        from .loader import load_level
        load_level(self, name)

    def make_scene(self):
        # setup the scene

        s = self.scene
        s.add(RailTrack(pyglet.resource.texture('track.png')))

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

    def shoot(self, source, direction, mask=MASK_ALL):
        p1 = source
        p2 = p1 + v(1000, random.uniform(-50, 50)) * direction
        seg = Segment(p1, p2)
        hit = self.physics.ray_query(seg, mask=mask)
        for d, obj in hit:
            vel = seg.edge

            if d <= 0:
                pos = seg.points[0]
                seg = None
            else:
                seg = seg.truncate(d)
                pos = seg.points[1]

            if hasattr(obj, 'hit'):
                obj.on_hit(pos, vel)

            break

        if seg:
            self.scene.add(Bullet(seg))

    def spawn_player(self):
        # all this should be done elsewhere
        start = v(90, 115)
        self.hero = Outlaw(start)
        self.hero.spawn(self)

    def process_input(self, keys):
        if self.hero.dead:
            return

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

        hr = self.hero.body.get_rect()
        for c in self.carriages:
            c.set_show_interior(c.intersects(hr))
            c.update(dt)
        for o in self.objects:
            o.update(dt)

    def update_ai(self, dt):
        for o in self.objects:
            if hasattr(o, 'ai'):
                o.ai.update(dt)
