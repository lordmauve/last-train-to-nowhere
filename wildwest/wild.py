import os
import sys

import pygame

sys.path.insert(0, '..')
import retrogamelib
from retrogamelib.gameobject import Object
from retrogamelib import display
from retrogamelib import clock
from retrogamelib import button
from retrogamelib.camera import Camera
from retrogamelib import util

ASSETS_BASE = 'assets/sprites'
IMG_PC_STANDING = os.path.join(ASSETS_BASE, 'pc-standing.png')
IMG_PC_CROUCHING = os.path.join(ASSETS_BASE, 'pc-crouching.png')
IMG_LAWMAN_STANDING = os.path.join(ASSETS_BASE, 'lawman-standing.png')
IMG_LAWMAN_CROUCHING = os.path.join(ASSETS_BASE, 'lawman-crouching.png')
IMG_TABLE = os.path.join(ASSETS_BASE, 'table.png')
IMG_CRATE = os.path.join(ASSETS_BASE, 'crate.png')
IMG_CARRIAGE = os.path.join(ASSETS_BASE, 'car-interior.png')


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


def main():
    display.init(1.0, 'Train to Nowhere', res=(1044, 400))

    objects = retrogamelib.gameobject.Group()
    carraiges = retrogamelib.gameobject.Group()
    players = retrogamelib.gameobject.Group()
    # bullets = retrogamelib.gameobject.Group()

    Carriage.groups = [carraiges, objects]
    Player.groups = [players, objects]
    Table.groups = [objects]
    Crate.groups = [objects]

    Carriage((10, 70))
    Hero((90, 145))
    Lawman((600, 165))
    Table((300, 212))
    Crate((500, 197))

    camera = Camera()
    # camera.center_at((-200, 50))

    while True:
        clock.tick()
        button.handle_input()
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
