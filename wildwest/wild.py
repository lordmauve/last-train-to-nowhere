import sys

sys.path.insert(0, '..')
# import retrogamelib
# from retrogamelib.constants import *
# from retrogamelib import geometry

import random

import pyglet
from pyglet.window import key
from pyglet import media


from .scenegraph import Scenegraph, Animation, AnimatedEffect, FloatyImage, StaticImage, FadeyImage
from .scenegraph import SkyBox, GroundPlane, Bullet, Depth
from .scenegraph.railroad import Locomotive, RailTrack, CarriageInterior, CarriageExterior
from .scenegraph.backgrounds import BackgroundFactory, FarBackgroundFactory

from .hud import HUD

from .svg import load_geometry
from .geom import v, Rect, Segment
from .physics import Body, StaticBody, Physics

from .sounds import GUNSHOT, PICKUP, THUD, GALLOP, Channel


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
GROUP_ALL = MASK_DEFAULT = 0x00ff
GROUP_PLAYER = 0x0001
GROUP_ENEMY = 0x0002
GROUP_SCENERY = 0x0004

GROUP_CORPSE = 0x0100


PUNCH_DAMAGE = 10


class Player(pyglet.event.EventDispatcher):
    MAX_WALK = 200  # limit on walk speed
    ACCEL = 120000  # acceleration when walking
    FRICTION = 1  # deceleration

    w = 32  # bounding box width
    h = 106  # bounding box height
    h_crouching = 70
    MASS = 100

    MAX_HEALTH = 100
    MIN_CROUCH_TIME = 0.15

    groups = GROUP_ALL  # collision groups
    attack = MASK_DEFAULT  # objects we can attack

    gold = 0    # gold bars collected

    Z = 1

    def __init__(self, pos, node):
        self.node = node
        node.z = self.Z
        self.body = Body(Rect.from_cwh(v(0, self.h / 2), self.w, self.h), self.MASS, pos, controller=self, groups=self.groups)
        self.running = 0
        self.crouching = False
        self.shooting = False
        self.hit = False
        self.dead = False
        self.can_change_crouch = True
        self.was_jumping = False
        self.direction = RIGHT

        self.health = self.MAX_HEALTH
        self.sound_channel = Channel()

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
        if self.dead:
            return
        self.dead = True
        self.health = 0
        self.node.play('dead')
        self.body.rect = Rect.from_blwh((-30, 0), 117, 24)
        self.body.apply_impulse(v(0, 100))
        self.body.groups = GROUP_CORPSE
        self.body.mask = 0x8000
        self.dispatch_event('on_death', self)

    @property
    def pos(self):
        return self.body.pos

    @property
    def jumping(self):
        return not self.body.on_floor

    def on_hit(self, pos, vel, damage=None):
        if damage is None:
            damage = random.uniform(11, 20)
        flip = v(1, 0).dot(vel) > 0

        if damage > 10:
            blood = AnimatedEffect('bloodspray.json', pos, 1.1)
            blood.set_flip(flip)
            self.world.scene.add(blood)

        self.health -= damage
        if self.health <= 0:
            self.die()
        else:
            if not self.shooting:
                self.node.play('hit')
            self.hit = True
            pyglet.clock.schedule_once(self.hit_finish, 0.3)

    def hit_finish(self, dt):
        """Called by a time to cancel the shooting animation."""
        self.hit = False

    def jump(self):
        if self.dead:
            return
        if not self.jumping and self.body.v.y < 20:
            self.body.apply_impulse(v(0, 450))
            self.node.play('jumping')

    def left(self):
        if self.dead:
            return
        if self.crouching:
            self.face_left()
            return
        self.running = -1
        self.body.apply_force(v(-self.ACCEL, 0))
        if not self.jumping:
            self.node.play('running')

    def right(self):
        if self.dead:
            return
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
        if self.dead or self.hit or not self.can_change_crouch:
            return
        self.running = 0
        if not self.crouching:
            self.body.rect = Rect.from_cwh(v(0, self.h_crouching / 2), self.w, self.h_crouching)
        self.set_crouching(True)

    def set_crouching(self, crouching):
        self.crouching = crouching
        if self.MIN_CROUCH_TIME:
            self.can_change_crouch = False
            pyglet.clock.schedule_once(self.cancel_crouch, self.MIN_CROUCH_TIME)

    def cancel_crouch(self, dt):
        self.can_change_crouch = True

    @property
    def hitlist(self):
        if self.crouching:
            off = v(self.direction * 69, 49)
        elif not self.jumping:
            off = v(self.direction * 58, 78)
        else:
            return []
        p1 = self.node.pos + off
        p2 = p1 + v(500, 0) * self.direction
        seg = Segment(p1, p2)
        hit = self.world.physics.ray_query(seg)
        return hit

    def on_pick_up(self, object):
        self.sound_channel.play(PICKUP)
        if isinstance(object, Health):
            self.health = min(self.health + 40, self.MAX_HEALTH)
        elif isinstance(object, GoldBar):
            self.gold += 1

    def shoot(self):
        if self.shooting or self.hit:
            return

        if not self.crouching:
            p1 = self.node.pos + v(0, 78) - v(20, 0) * self.direction
            p2 = p1 + v(80, 0) * self.direction
            seg = Segment(p1, p2)
            hit = self.world.physics.ray_query(seg, mask=self.attack)
            for d, obj in hit:
                if isinstance(obj, Player):
                    self.do_punch(seg, hit)
                    return
        self.do_shoot()

    def do_punch(self, seg, objs):
        self.shooting = True
        self.node.play('punching')

        vel = seg.edge
        for d, obj in objs:
            pos = seg.truncate(d).points[1]
            obj.on_hit(pos, vel, PUNCH_DAMAGE)

        pyglet.clock.schedule_once(self.shooting_finish, 0.5)

    def do_shoot(self):
        self.sound_channel.play(GUNSHOT)
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

        if self.was_jumping and not self.jumping:
            self.sound_channel.play(THUD)
            self.was_jumping = False

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
            self.was_jumping = True
        else:
            if abs(vx) < 50 and not self.running:
                self.body.v = v(0, self.body.v.y)
                self.node.play('standing')
            else:
                self.node.play('running')

        if self.can_change_crouch:
            self.set_crouching(False)

        if not self.crouching:
            self.body.rect = Rect.from_cwh(v(0, self.h / 2), self.w, self.h)
        self.running = 0


Player.register_event_type('on_death')


class Lawman(Player):
    groups = GROUP_ENEMY     # collision groups
    attack = MASK_DEFAULT & ~GROUP_ENEMY  # objects we can attack

    MAX_HEALTH = 40
    MIN_CROUCH_TIME = 0.3

    def __init__(self, pos):
        node = Animation('lawman.json', pos)
        super(Lawman, self).__init__(pos, node)


class Outlaw(Player):
    groups = GROUP_PLAYER     # collision groups
    attack = MASK_DEFAULT & ~GROUP_PLAYER

    MAX_HEALTH = 120
    MIN_CROUCH_TIME = 0

    Z = 1.01

    def __init__(self, pos):
        node = Animation('pc.json', pos)
        super(Outlaw, self).__init__(pos, node)


class OutlawOnHorse(object):
    VELOCITY = v(40, 0)
    dead = False
    body = None

    FADE = 0.9

    def __init__(self, pos):
        self.pos = pos
        self.spawned = False  # has the player jumped off?
        self.anim = Animation('pc-horse.json', pos, z=2)
        self.node = Depth(self.anim, 1)
        self.node.pos = pos

        self.hero = Outlaw(v(15, 115))
        
        self.gallop = media.Player()
        self.gallop.queue(GALLOP)

    def spawn(self, world):
        self.world = world
        world.scene.add(self.node)
        world.objects.append(self)
        self.gallop.eos_action = media.Player.EOS_LOOP
        self.gallop.play()

    def kill(self):
        self.node.scenegraph.remove(self.node)
        self.world.objects.remove(self)
        self.gallop.pause()

    def __del__(self):
        self.gallop.pause()

    def noop(self):
        """Don't accept input."""

    left = noop
    right = noop
    down = noop
    jump = noop

    def shoot(self):
        self.pos = v(15, 0)

    def start_player(self):
        self.hero.spawn(self.world)
        self.world.hero = self.hero
        
        hud = HUD(self.hero)
        self.world.scene.add(hud)
        self.world.hud = hud
        
        self.anim.play('horse')
        self.VELOCITY = -self.VELOCITY

    def update(self, dt):
        if self.spawned:
            self.gallop.volume *= self.FADE ** dt
        self.pos += self.VELOCITY * dt
        self.node.pos = self.pos
        if self.pos.x > 15 and not self.spawned:
            self.start_player()
            self.spawned = True
        if self.pos.x < -1020:
            self.kill()


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


class Tanker(object):
    WIDTH = 742

    def __init__(self, pos):
        pos = v(1, 0).project(pos)
        self.interior = CarriageInterior(pos, 'tanker')
        self.body = StaticBody(load_geometry('tanker'), v(0, 53) + pos)

    def get_pos(self):
        return self.interior.pos

    def set_pos(self, pos):
        self.interior.pos = pos
        self.body.pos = v(0, 53) + pos

    pos = property(get_pos, set_pos)

    def spawn(self, world):
        world.physics.add_static(self.body)
        world.scene.add(self.interior)

    def remove(self, scenegraph):
        scenegraph.remove(self.interior)

    def intersects(self, rect):
        return False

    def set_show_interior(self, show):
        pass


class LocomotiveObject(object):
    GOAL = Rect.from_blwh(v(308, 178), 155, 138)

    def __init__(self, pos):
        pos = v(1, 0).project(pos)
        self.node = Locomotive(pos)
        self.body = StaticBody(load_geometry('locomotive'), pos)
        self.goal = self.GOAL.translate(pos)

    def spawn(self, world):
        self.world = world
        world.scene.add(self.node)
        world.physics.add_static(self.body)
        world.objects.append(self)

    def update(self, dt):
        hero = self.world.get_hero()
        if hero:
            r = hero.body.get_rect()
            if r.intersects(self.goal):
                self.world.in_goal(hero)


class Pickup(object):
    def __init__(self, pos):
        self.pos = pos
        self.node = FloatyImage(pos, self.IMAGE, 0)

    def spawn(self, world):
        self.world = world
        world.objects.append(self)
        world.scene.add(self.node)

    def kill(self):
        self.world.objects.remove(self)
        self.world.scene.remove(self.node)

    def get_rect(self):
        return self.RECT.translate(self.pos)

    def update(self, dt):
        h = self.world.get_hero()
        if h:
            if h.body.get_rect().intersects(self.get_rect()):
                h.on_pick_up(self)
                self.kill()


class Health(Pickup):
    RECT = Rect.from_blwh((0, 0), 49, 32)
    IMAGE = 'health.png'


class GoldBar(Pickup):
    RECT = Rect.from_blwh((0, 0), 36, 31)
    IMAGE = 'goldbar.png'


class Scenery(object):
    Z = -0.2
    def __init__(self, pos):
        self.pos = pos
        self.node = StaticImage(pos, self.IMAGE, self.Z)

    def spawn(self, world):
        self.world = world
        world.scene.add(self.node)

    def kill(self):
        self.world.scene.remove(self.node)


class ForegroundScenery(Scenery):
    Z = 1.9


class Light(ForegroundScenery):
    IMAGE = 'light.png'


class Seats(Scenery):
    IMAGE = 'seats.png'


class PhysicalScenery(object):
    _geometries = {}

    def __init__(self, pos):
        self.node = StaticImage(pos, self.IMAGE, z=0)
        rect = self.load_geometry()
        self.body = Body(rect, self.MASS, pos, controller=self, groups=GROUP_SCENERY)

    def load_geometry(self):
        try:
            return self._geometries[self.GEOMETRY]
        except KeyError:
            rect = load_geometry(self.GEOMETRY)[0]
            self._geometries[self.GEOMETRY] = rect
            return rect

    def spawn(self, world):
        world.physics.add_body(self.body)
        world.scene.add(self.node)
        world.objects.append(self)

    def update(self, dt):
        self.node.pos = self.body.pos


class StaticScenery(PhysicalScenery):
    def __init__(self, pos):
        self.node = StaticImage(pos, self.IMAGE, z=0)
        rect = self.load_geometry()
        self.body = StaticBody([rect], pos)

    def spawn(self, world):
        world.physics.add_static(self.body)
        world.scene.add(self.node)

    def update(self, dt):
        pass


class Crate(StaticScenery):
    IMAGE = 'crate.png'
    GEOMETRY = 'crate'


class Hatch(StaticScenery):
    IMAGE = 'hatch.png'
    GEOMETRY = 'hatch'


class MailSack(PhysicalScenery):
    IMAGE = 'mailsack.png'
    GEOMETRY = 'mailsack'
    MASS = 2000


class Table(PhysicalScenery):
    IMAGE = 'table.png'
    GEOMETRY = 'table'
    MASS = 100


class World(pyglet.event.EventDispatcher):
    """Collection of all the objects and geometry in the world."""

    GOLD_NEEDED = 3

    def __init__(self):
        self.objects = []
        self.carriages = []

        self.physics = Physics()

        self.scene = Scenegraph()
        self.make_scene()

    def load_level(self, name):
        from .loader import load_level
        load_level(self, name)

        bars = self.GOLD_NEEDED
        bars -= len(self.get_objects_by_class(GoldBar))

        if bars > 0:
            lawmen = self.get_objects_by_class(Lawman)
            num = min(len(lawmen), bars)
            holding_bars = random.sample(lawmen, num)
            for lm in holding_bars:
                lm.gold = 1
                lm.set_handler('on_death', self.drop_bar)
            bars -= num

        # Reduce the requirement if we still can't satisfy it
        self.GOLD_NEEDED -= bars

    def drop_bar(self, char):
        if not char.gold:
            return
        pos = char.pos
        GoldBar(pos).spawn(self)
        char.gold = 0

    def in_goal(self, char):
        if char.gold >= self.GOLD_NEEDED:
            self.dispatch_event('on_goal', char)
        else:
            self.scene.add(self.moregold)
            self.moregold.pos = char.pos + v(-206, 200)
            self.moregold.show()

    def get_objects_by_class(self, cls):
        objs = []
        for o in self.objects:
            if isinstance(o, cls):
                objs.append(o)
        return objs

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

        s.add(BackgroundFactory())
        s.add(FarBackgroundFactory())

        self.moregold = FadeyImage(v(0, 0), 'moregold.png', 10)
        return s

    def shoot(self, source, direction, mask=MASK_DEFAULT):
        p1 = source
        p2 = p1 + v(500, random.normalvariate(0, 12.5)) * direction
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

    def is_hero_alive(self):
        return self.hero.body and not self.hero.dead

    def get_hero(self):
        if not self.is_hero_alive():
            return None
        return self.hero

    def spawn_player(self):
        # all this should be done elsewhere
        start = v(-400, 0)
        self.hero = OutlawOnHorse(start)
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

        if self.is_hero_alive():
            hr = self.hero.body.get_rect()
            for c in self.carriages:
                c.set_show_interior(c.intersects(hr))
                c.update(dt)

        for o in self.objects:
            o.update(dt)
            if hasattr(o, 'ai'):
                if not o.dead:
                    o.ai.update_frame(dt)

    def update_ai(self, dt):
        if self.is_hero_alive():
            for o in self.objects:
                if hasattr(o, 'ai'):
                    if not o.dead:
                        o.ai.update(dt)


World.register_event_type('on_goal')
