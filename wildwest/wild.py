import sys

sys.path.insert(0, '..')
# import retrogamelib
# from retrogamelib.constants import *
# from retrogamelib import geometry

import pyglet
from pyglet.window import key
from scenegraph import StaticImage, Scenegraph, Fill, RailTrack
from scenegraph import SkyBox, GroundPlane, Wheels
from scenegraph import Camera
from vector import Vector

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

FLOOR_Y = 275


class Bullet(StaticImage):
    pass


class Player(StaticImage):
    MAX_WALK = 200  # limit on walk speed
    ACCEL = 1600  # acceleration when walking
    FRICTION = 1  # deceleration

    def __init__(self, pos, img_path):
        StaticImage.__init__(self, pos, img_path)
        self.direction = Vector((1, 0))
        self.t = 0
        self.walk_speed = 0
        self.xaccel = 0
        self.jump_speed = 10
        self.jumping = False
        self.on_floor = False
        # self.fall_through = 0  # frames of fall_through

    def on_key_press(self, symbol, modifiers):
        if symbol == KEY_JUMP:
            self.jump()
        if symbol == KEY_SHOOT:
            self.shoot()
        if symbol in (KEY_LEFT, KEY_RIGHT):
            self.walk(symbol)
        # self.aim_shot()
        # self.choose_images()

    def jump(self):
        if not self.on_floor:
            return
        self.jumping = True
        self.jump_speed = -12
        # if not self.jumping:
        #     self.jumping = True
        #     if button.is_held(DOWN):
        #         self.jump_speed = 7
        #         # self.fall_through = 4
        #     else:
        #         self.jump_speed = -11
        #     print 'jump_speed:', self.jump_speed

    def walk(self, symbol):
        if symbol == key.LEFT:
            self.xaccel = -self.ACCEL
        elif symbol == key.RIGHT:
            self.xaccel = self.ACCEL

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

    def draw(self, camera):
        dt = self.scenegraph.t - self.t
        self.t = self.scenegraph.t

        # update horizontally
        u = self.walk_speed
        self.walk_speed += self.xaccel * dt
        if abs(self.walk_speed) > self.MAX_WALK:
            self.walk_speed = self.MAX_WALK * self.walk_speed / abs(self.walk_speed)
        self.sprite.x += 0.5 * (u + self.walk_speed) * dt

        super(Player, self).draw(camera)

        # update acceleration
        if abs(self.walk_speed) < 0.01:
            self.walk_speed = 0
            self.xaccel = 0
        else:
            self.xaccel = -self.FRICTION * self.walk_speed

        # update vertically
        # # if self.jump_speed < 7:
        # #     self.jump_speed += 1
        # # if self.jump_speed < 10 and\
        # if (self.jumping or self.sprite.y < FLOOR_Y - self.sprite.height):
        #     self.jump_speed += 1
        #     self.sprite.y += self.jump_speed
        #     if self.sprite.y > FLOOR_Y - self.sprite.height:
        #         self.sprite.y = FLOOR_Y - self.sprite.height
        #     #print 'jump_speed: %d, rect.y: %d' % (self.jump_speed, self.rect.y)

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


def main():
    WIDTH = 800
    HEIGHT = 600
    w = pyglet.window.Window(width=800, height=600)
    s = Scenegraph()

    s.add(Fill((1.0, 1.0, 1.0, 1.0)))
    s.add(Carriage((0, 53)))
    s.add(Hero((90, 115)))
    s.add(Lawman((600, 115)))
    s.add(Table((300, 115)))
    s.add(Crate((500, 115)))
    s.add(RailTrack(pyglet.resource.texture('track.png')))
    s.add(Wheels((91, 0)))
    s.add(Wheels((992 - 236, 0)))

    ground = GroundPlane(
        (218, 176, 127, 255),
        (194, 183, 164, 255),
    )
    s.add(ground)

    s.add(SkyBox(
        (129, 218, 255, 255),
        (49, 92, 142, 255)
    ))

    camera = Camera((200.0, 200.0), WIDTH, HEIGHT)

    @w.event
    def on_draw():
        s.draw(camera)

    @w.event
    def on_key_press(symbol, modifiers):
        s.on_key_press(symbol, modifiers)

    def update(dt):
        s.update(dt)

    pyglet.clock.schedule_interval(update, 1 / 30.0)
    pyglet.app.run()


if __name__ == '__main__':
    main()
