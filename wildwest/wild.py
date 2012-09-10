import sys

sys.path.insert(0, '..')
# import retrogamelib
# from retrogamelib.constants import *
# from retrogamelib import geometry

import pyglet
from pyglet.window import key
from scenegraph import StaticImage, Scenegraph, Fill, RailTrack
from scenegraph import SkyBox, GroundPlane, Wheels, Locomotive
from scenegraph import Camera
from geom import v


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
KEY_JUMP = key.Z
KEY_SHOOT = key.X



FLOOR_Y = 115
GRAVITY = 1200


class Bullet(StaticImage):
    pass


class Player(object):
    MAX_WALK = 200  # limit on walk speed
    ACCEL = 2000  # acceleration when walking
    FRICTION = 1  # deceleration

    w = 42  # bounding box width
    h = 84  # bounding box height

    def __init__(self, pos, node):
        self.pos = pos
        self.node = node
        self.direction = v(1, 0)
        self.v = v(0, 0)
        self.xaccel = 0
        self.on_floor = True
        # self.fall_through = 0  # frames of fall_through
        # self.aim_shot()
        # self.choose_images()

    def jump(self):
        if not self.on_floor:
            return
        self.jumping = True
        self.v += v(0, 400)  # Apply jumping impulse
        self.on_floor = False
        # if not self.jumping:
        #     self.jumping = True
        #     if button.is_held(DOWN):
        #         self.jump_speed = 7
        #         # self.fall_through = 4
        #     else:
        #         self.jump_speed = -11
        #     print 'jump_speed:', self.jump_speed

    def left(self):
        self.xaccel = -self.ACCEL

    def right(self):
        self.xaccel = self.ACCEL

    def shoot(self):
        """Not yet implemented!"""

    # def aim_shot(self):
    #     self.shot_vector = self.direction.copy()
    #     x = int(button.is_held(RIGHT) - button.is_held(LEFT))
    #     y = int(button.is_held(DOWN) - button.is_held(UP))
    #     if not x and y > 0 and not self.jumping:
    #         y = 0
    #     if y:
    #         self.shot_vector.x = x
    #     self.shot_vector.y = y

    # def do_walk(self):
    #     if self.walk_speed:
    #         self.rect.x = int(self.rect.x + self.walk_speed)
    #         self.direction.x = self.walk_speed / abs(self.walk_speed)


    def update(self, dt):
        # work out our new velocity
        u = self.v
        vx = u.x + self.xaccel * dt
        vx = max(-self.MAX_WALK, min(self.MAX_WALK, vx))
        vy = u.y - GRAVITY * dt
        self.v = v(vx, vy)

        # work out our new position
        # Constant acceleration formulae
        self.pos += 0.5 * (u + self.v) * dt

        # So far so mechanical. Now we have to take into account collisions and friction etc.
        
        # update acceleration
        if abs(self.v.x) < 0.01:
            self.v = v(0, self.v.y)
            self.xaccel = 0
        else:
            self.xaccel = -self.FRICTION * self.v.x

        # Collision with floor
        x, y = self.pos
        if y <= FLOOR_Y:
            y = FLOOR_Y
            self.on_floor = True
            self.v = v(self.v.x, 0)
        else:
            self.on_floor = False

        self.pos = v(x, y)
        self.node.pos = self.pos

        # #self.do_walk()
        # self.on_floor = False
        # self.collide_with_floors()
        # # if self.fall_through > 0:
        # #     self.fall_through -= 1

    def collide_with_floors(self):
        # print list(self.platforms)
        # for platform in self.platforms:
            # if self.fall_through and\
            #         platform.allow_fall_through and\
            #         self.jump_speed > 3:
            #     continue
            # if self.rect.colliderect(platform.rect):
            #     if self.jump_speed >= 0:
            #         if self.rect.bottom < platform.rect.top + (self.jump_speed*2):
            #             self.rect.bottom = platform.rect.top
            #             self.hit_floor()
        if self.rect.y >= FLOOR_Y - self.rect.height:
            self.hit_floor()

    def hit_floor(self):
        # print 'hit the floor'
        self.jump_speed = 10
        self.on_floor = True
        self.jumping = False


class Table(StaticImage):
    def __init__(self, pos):
        StaticImage.__init__(self, pos, IMG_TABLE)


class Crate(StaticImage):
    def __init__(self, pos):
        StaticImage.__init__(self, pos, IMG_CRATE)


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
#    s.add(Crate((500, 115)))
    s.add(RailTrack(pyglet.resource.texture('track.png')))
    s.add(Wheels((91, 0)))
    s.add(Wheels((992 - 236, 0)))
    s.add(Locomotive((1070, 0)))

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
        self.actors = []
        self.static = []


FPS = 30


class Game(object):
    def __init__(self):
        WIDTH = 800
        HEIGHT = 600
        self.window = pyglet.window.Window(width=WIDTH, height=HEIGHT)
        self.scene = make_scene()
        self.camera = Camera((200.0, 200.0), WIDTH, HEIGHT)
        self.keys = key.KeyStateHandler() 
        self.window.push_handlers(self.keys)
        self.window.push_handlers(
            on_draw=self.draw
        )
        self.spawn_player()
        pyglet.clock.schedule_interval(self.update, 1.0 / FPS)

    def spawn_player(self):
        # all this should be done elsewhere
        start = v(90, 115)
        node = StaticImage(start, 'pc-standing.png')
        self.scene.add(node)
        self.hero = Player(start, node)

    def draw(self):
        self.scene.draw(self.camera)

    def process_input(self):
        if self.keys[KEY_LEFT]:
            self.hero.left()
        elif self.keys[KEY_RIGHT]:
            self.hero.right()

        if self.keys[KEY_JUMP]:
            self.hero.jump()
        elif self.keys[KEY_SHOOT]:
            self.hero.shoot()

    def update(self, dt):
        self.process_input()
        self.hero.update(dt)

        self.camera.offset = self.hero.pos + v(0, 120)
        self.scene.update(dt)


def main():
    g = Game()
    pyglet.app.run()


if __name__ == '__main__':
    main()
