import math

import pyglet
from pyglet import gl

from ..vector import v
from . import Node, AnimatedNode, StaticImage, CompoundNode, Depth


class Wheels(Node):
    z = -1.9

    def __init__(self, pos):
        from pyglet.image import Animation, AnimationFrame
        im1 = pyglet.resource.image('wheels.png')
        im2 = pyglet.resource.image('wheels2.png')
        im3 = pyglet.resource.image('wheels3.png')
        t = 0.05
        anim = Animation([
            AnimationFrame(im1, t),
            AnimationFrame(im2, t),
            AnimationFrame(im3, t),
        ])
        self.sprite1 = pyglet.sprite.Sprite(anim)
        self.sprite2 = pyglet.sprite.Sprite(anim)
        self.sprite2.color = (64, 64, 64)
        self.pos = pos

    def get_position(self):
        return self.sprite1.position

    def set_position(self, pos):
        self.sprite1.position = pos
        self.sprite2.position = pos

    pos = property(get_position, set_position)

    def draw(self, camera):
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, -70)
        self.sprite2.draw()
        gl.glPopMatrix()
        self.sprite1.draw()


class LocomotiveWheel(AnimatedNode):
    z = 1
    def __init__(self, pos):
        wheel = pyglet.resource.image('locomotive-wheel.png')
        wheel.anchor_x = wheel.width // 2
        wheel.anchor_y = wheel.height // 2
        super(LocomotiveWheel, self).__init__(pos, wheel, 1)

    def draw(self, camera):
        angle = (self.scenegraph.t * 360) % 25
        self.sprite.rotation = angle
        super(LocomotiveWheel, self).draw(camera)


class WheelBar(StaticImage):
    RADIUS = 50
    CONNECTED_LENGTH = 180  # distance between the wheels

    def __init__(self, pos):
        super(WheelBar, self).__init__(pos, 'wheel-bar.png', 2)
        im = self.sprite.image
        im.anchor_x = 12
        im.anchor_y = 12
        self.sprite2 = pyglet.sprite.Sprite(im)
        
        pb = pyglet.resource.image('piston-bar.png')
        pb.anchor_x = 17
        pb.anchor_y = 17
        self.pistonbar = pyglet.sprite.Sprite(pb)

        p = pyglet.resource.image('piston.png')
        p.anchor_y = 21
        self.piston = pyglet.sprite.Sprite(p)
        self.piston.position = self._pos + v(2.5 * self.CONNECTED_LENGTH, 0)

    def draw(self, camera):
        a = self.scenegraph.t * math.pi * 7
        off = v(
            self.RADIUS * math.sin(a),
            self.RADIUS * math.cos(a),
        )
        self.sprite.position = v(self._pos) + off

        a2 = math.asin(off.y / self.CONNECTED_LENGTH)
        self.sprite2.rotation = math.degrees(a2)
        self.sprite2.position = v(self.sprite.position) + v(self.CONNECTED_LENGTH, 0)
        super(WheelBar, self).draw(camera)
        self.sprite2.draw()
        self.pistonbar.position = v(
            off.x + self.CONNECTED_LENGTH + self.CONNECTED_LENGTH * math.cos(a2),
            0
        ) + self._pos
        self.pistonbar.draw()
        self.piston.draw()


class Locomotive(CompoundNode):
    z = 1

    def build(self):
        self.add_child(StaticImage((0, 0), 'locomotive.png'))
        self.add_child(Wheels((60, 0)))

        wheels = CompoundNode(children=[
            LocomotiveWheel((303 + 82, 82)),
            LocomotiveWheel((303 + 180 + 82, 82))
        ])

        # Link the same object into the scenegraph twice! Ooo-err...
        self.add_child(wheels)
        self.add_child(Depth(wheels, -70))

        self.add_child(WheelBar((303 + 82, 82)))


class RailTrack(Node):
    z = -2
    def __init__(self, tex, y=0):
        self.y = y
        self.group = pyglet.sprite.SpriteGroup(
            tex,
            gl.GL_SRC_ALPHA,
            gl.GL_ONE_MINUS_SRC_ALPHA
        )

    def draw(self, camera):
        dist = 779 * self.scenegraph.t
        vp = camera.viewport()

        l = vp.l - 128
        r = vp.r + 128
        scale = vp.w / 128
        coords = ('v3f', [
            l, self.y, 32,
            r, self.y, 32,
            r, self.y, -96,
            l, self.y, -96,
        ])
        d = dist / 128.0
        tc = ('t2f', [
            1, d,
            1, d + scale,
            0, d + scale,
            0, d
        ])
        self.group.set_state()
        pyglet.graphics.draw(4, gl.GL_QUADS, coords, tc)
        self.group.unset_state()


