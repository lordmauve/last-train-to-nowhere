import os
import sys

import pygame

sys.path.insert(0, '..')
import retrogamelib
from retrogamelib.gameobject import Object
from retrogamelib import display
from retrogamelib import clock
from retrogamelib import button
from retrogamelib.constants import *
from retrogamelib.camera import Camera
from retrogamelib import util
from retrogamelib import geometry

ASSETS_BASE = 'assets/sprites'
IMG_PC_STANDING = os.path.join(ASSETS_BASE, 'pc-standing.png')
IMG_PC_CROUCHING = os.path.join(ASSETS_BASE, 'pc-crouching.png')
IMG_LAWMAN_STANDING = os.path.join(ASSETS_BASE, 'lawman-standing.png')
IMG_LAWMAN_CROUCHING = os.path.join(ASSETS_BASE, 'lawman-crouching.png')
IMG_TABLE = os.path.join(ASSETS_BASE, 'table.png')
IMG_CRATE = os.path.join(ASSETS_BASE, 'crate.png')
IMG_CARRIAGE = os.path.join(ASSETS_BASE, 'car-interior.png')

FLOOR_Y = 400


class Bullet(Object):
    pass


class ImageObject(Object):
    def __init__(self, pos, img_path):
        Object.__init__(self, self.groups)
        self.image = util.load_image(img_path)
        self.rect = self.image.get_rect(topleft=pos)


class Player(ImageObject):
    def __init__(self, pos, img_path):
        ImageObject.__init__(self, pos, img_path)
        self.direction = geometry.Vector(1, 0)
        self.walk_speed = 0
        self.jump_speed = 0
        self.jumping = False
        self.on_floor = False
        self.fall_through = 0  # frames of fall_through

    def controls(self):
        if button.is_pressed(A_BUTTON):
            self.jump()
        if button.is_pressed(B_BUTTON):
            self.shoot()
        self.control_walk()
        # self.aim_shot()
        # self.choose_images()

    def jump(self):
        print 'jumping'
        if not self.on_floor:
            return
        if not self.jumping:
            self.jumping = True
            if button.is_held(DOWN):
                self.jump_speed = 7
                self.fall_through = 4
            else:
                self.jump_speed = -11
            print 'jump_speed:', self.jump_speed

    def control_walk(self):
        self.walk_speed = 0
        if button.is_held(LEFT):
            self.walk_speed -= 3
        if button.is_held(RIGHT):
            self.walk_speed += 3

    # def aim_shot(self):
    #     self.shot_vector = self.direction.copy()
    #     x = int(button.is_held(RIGHT) - button.is_held(LEFT))
    #     y = int(button.is_held(DOWN) - button.is_held(UP))
    #     if not x and y > 0 and not self.jumping:
    #         y = 0
    #     if y:
    #         self.shot_vector.x = x
    #     self.shot_vector.y = y

    def do_walk(self):
        if self.walk_speed:
            self.rect.x += self.walk_speed
            self.direction.x = self.walk_speed / abs(self.walk_speed)

    def update(self):
        # if self.jump_speed < 7:
        #     self.jump_speed += 1
        if self.jump_speed < 0:
            self.rect.y += self.jump_speed

        self.do_walk()
        self.on_floor = False
        self.collide_with_floors()
        if self.fall_through > 0:
            self.fall_through -= 1

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
        if self.rect.right >= FLOOR_Y:
            self.hit_floor()

    def hit_floor(self):
        self.jump_speed = 3
        self.on_floor = True
        self.jumping = False


class Table(ImageObject):
    def __init__(self, pos):
        ImageObject.__init__(self, pos, IMG_TABLE)


class Crate(ImageObject):
    def __init__(self, pos):
        ImageObject.__init__(self, pos, IMG_CRATE)


class Hero(Player):
    def __init__(self, pos):
        Player.__init__(self, pos, IMG_PC_STANDING)


class Lawman(Player):
    def __init__(self, pos):
        Player.__init__(self, pos, IMG_LAWMAN_STANDING)


class Carriage(Object):
    def __init__(self, pos):
        Object.__init__(self, self.groups)
        image = util.load_image(IMG_CARRIAGE)
        self.image = pygame.transform.scale(image, (1024, 319))
        self.rect = self.image.get_rect(topleft=pos)
        self.allow_fall_through = False


def main():
    display.init(1.0, 'Train to Nowhere', res=(1044, 400))

    objects = retrogamelib.gameobject.Group()
    platforms = retrogamelib.gameobject.Group()
    players = retrogamelib.gameobject.Group()
    # bullets = retrogamelib.gameobject.Group()

    Carriage.groups = [platforms, objects]
    Player.groups = [players, objects]
    Table.groups = [objects]
    Crate.groups = [objects]
    Player.platforms = platforms

    Carriage((10, 70))
    hero = Hero((90, 167))
    Lawman((600, 165))
    Table((300, 222))
    Crate((500, 197))

    camera = Camera()
    camera.follow(hero)

    while True:
        clock.tick()
        button.handle_input()
        for o in objects:
            o.update()
        hero.controls()
        camera.update()

        surface = display.surface
        surface.fill((0, 0, 180))

        for object in objects:
            translated = camera.translate(object.rect)
            surface.blit(object.image, translated)
            if translated.x < -16 or translated.x > 300:
                if hasattr(object, 'offscreen'):
                    object.offscreen(camera)
            else:
                if hasattr(object, 'onscreen'):
                    object.onscreen(camera)

        display.update()

if __name__ == '__main__':
    main()
