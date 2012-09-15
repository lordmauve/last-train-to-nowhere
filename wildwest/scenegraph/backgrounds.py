import random

import pyglet
from pyglet import gl

from weakref import WeakSet

from ..geom import v, Rect
from . import Node, SpriteNode


class BackgroundObject(SpriteNode):
    SPEED = 300

    def __init__(self, pos, image, z, scale=1.0):
        super(BackgroundObject, self).__init__(pos, image, z)
        self.t = None
        self.sprite.scale = scale
        self.rect = Rect.from_blwh(pos, image.width * scale, image.height * scale)

    def draw(self, camera):
        if self.t is None:
            self.t = self.scenegraph.t

        xoff = (self.scenegraph.t - self.t) * self.SPEED
        vp = camera.get_plane_rect(-self.z + camera.focus)
        r = self.rect.translate(v(-xoff, 0))
        if r.r < vp.l:
            self.scenegraph.remove(self)

        gl.glPushMatrix()
        gl.glTranslatef(-xoff, 0, self.z)
        super(BackgroundObject, self).draw(camera)
        gl.glPopMatrix()



class BackgroundFactory(Node):
    SPRITES = [
        'cactus1.png',
        'cactus2.png',
        'cactus3.png',
        'cactus4.png',
        'pebble1.png',
        'pebble2.png',
        'pebble3.png',
        'rock1.png',
    ]

    INTERVAL = 0.5
    MAX_OBJECTS = 30
    SCALE = 1.0

    def __init__(self):
        self.load_sprites()
        self.last_t = None
        self.objects = WeakSet()

    def load_sprites(self):
        self.sprites = [pyglet.resource.image(s) for s in self.SPRITES]

    def random_dist(self, camera):
        return random.uniform(camera.focus * 1.5, camera.far * 0.95)

    def spawn(self, camera, anywhere=False):
        s = random.choice(self.sprites)
        z = self.random_dist(camera)
        bounds = camera.get_plane_rect(z + camera.focus)
        if anywhere: 
            pos = v(random.uniform(bounds.l, bounds.r), 0)
        else:
            pos = v(bounds.r, 0)
        o = BackgroundObject(pos, s, -z, self.SCALE)
        self.scenegraph.add(o)
        self.objects.add(o)

    def populate(self, camera):
        for i in xrange(30):
            self.spawn(camera, True)

    def draw(self, camera):
        if self.last_t is None:
            self.last_t = self.scenegraph.t
            self.populate(camera)
            return
        
        if self.scenegraph.t - self.last_t > self.INTERVAL and len(self.objects) < self.MAX_OBJECTS:
            self.spawn(camera)
            self.last_t = self.scenegraph.t


class FarBackgroundFactory(BackgroundFactory):
    SCALE = 7
    SPRITES = [
        'hill1.png',
        'hill2.png',
        'hill3.png',
    ]
    INTERVAL = 2

    def random_dist(self, camera):
        return random.uniform(camera.far * 0.8 - camera.focus, camera.far - camera.focus)
