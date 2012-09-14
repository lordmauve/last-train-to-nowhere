import os
import json
import math

import pyglet
from pyglet import gl
import pyglet.image.atlas

from itertools import chain

from ..geom import Rect, v


def _texture_atlas_add(self, img):
    """Monkey patch pyglet to pad the texture atlas to remove adjacency artifacts.

    Taken from http://markmail.org/message/qn65kjlieq6n333k
    """
    pad = 1
    x, y = self.allocator.alloc(img.width + pad * 2, img.height + pad * 2)
    self.texture.blit_into(img, x + pad, y + pad, 0)
    region = self.texture.get_region(x + pad, y + pad, img.width, img.height)
    return region

pyglet.image.atlas.TextureAtlas.add = _texture_atlas_add


pyglet.resource.path += [
    './assets/sprites',
    './assets/textures',
    '../assets/sprites',
    '../assets/textures',
]
pyglet.resource.reindex()


class Camera(object):
    """A camera object."""
    def __init__(self, offset, screen_w, screen_h):
        self.near = 1.0
        self.focus = 800.0  # the plane our 2D scene is mainly on
        self.far = 10000.0
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.offset = v(offset)

    def get_plane_rect(self, depth):
        """Get the rectangle of a plane perpendicular to the view direction,
        a distance depth from the camera."""
        scale = depth / self.focus
        x, y = self.offset

        # The extra 1/1.01 is to cover the distance from the centre of the
        # outside pixels to the edge of the frustum
        sw = self.screen_w + 1.001
        sh = self.screen_h + 1.001

        return Rect(
            x + scale * -0.5 * sw,
            x + scale * 0.5 * sw,
            y + scale * -0.5 * sh,
            y + scale * 0.5 * sh
        )

    def far_plane(self):
        """Get the rectangle of the back plane"""
        return self.get_plane_rect(self.far)

    def near_plane(self):
        """Get the rectangle of the near plane"""
        return self.get_plane_rect(self.near)
    
    def viewport(self):
        """Get the rectangle of the near plane"""
        x, y = self.offset
        return Rect(
            x + -0.5 * self.screen_w,
            x + 0.5 * self.screen_w,
            y + -0.5 * self.screen_h,
            y + 0.5 * self.screen_h,
        )

    def setup_matrixes(self):
        x, y = self.offset
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
#        fov = math.atan(self.screen_h * 0.5 / self.focus)
#        aspect = self.screen_w * 1.0 / self.screen_h
#        gl.gluPerspective(fov, aspect, self.near, self.far)
        l = -0.5 * self.screen_w / (self.focus - self.near)
        r = -l
        b = -0.5 * self.screen_h / (self.focus - self.near)
        t = -b
        self.np = Rect(l, r, b, t)
        gl.glFrustum(l, r, b, t, self.near, self.far)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glTranslatef(-x, -y, -self.focus)


class Node(object):
    """Base class for scenegraph objects."""
    z = 0
    scenegraph = None

    def set_scenegraph(self, scenegraph):
        self.scenegraph = scenegraph


class CompoundNode(Node):
    def __init__(self, pos=(0, 0), children=()):
        self.pos = v(pos)
        self.children = []
        for c in children:
            self.add_child(c)
        self.build()

    def set_scenegraph(self, scenegraph):
        self.scenegraph = scenegraph
        for c in self.children:
            c.set_scenegraph(scenegraph)

    def build(self):
        """Subclasses can override this to populate the node."""

    def add_child(self, c):
        assert isinstance(c, Node), '%r is not a Node' % c
        c.set_scenegraph(self.scenegraph)
        self.children.append(c)

    def remove_child(self, c):
        c.set_scenegraph(None)
        self.children.remove(c)

    def draw(self, camera):
        self.children.sort(key=lambda x: x.z)
        gl.glPushMatrix()
        gl.glTranslatef(self.pos.x, self.pos.y, 0)
        for c in self.children:
            c.draw(camera)
        gl.glPopMatrix()


class SpriteNode(Node):
    def __init__(self, pos, animation, z=0):
        self.z = z
        self.sprite = pyglet.sprite.Sprite(animation)
        self.pos = v(pos)

    def get_position(self):
        return self._pos

    def set_position(self, pos):
        self._pos = pos
        self.sprite.position = pos

    pos = property(get_position, set_position)

    def draw(self, camera):
        self.sprite.draw()


class StaticImage(SpriteNode):
    def __init__(self, pos, img, z=-1):
        im = pyglet.resource.image(img)
        super(StaticImage, self).__init__(pos, im, z)


class Animation(SpriteNode):
    """Node that loads multiple animations from a JSON file.
    
    The current animation can be changed using .play()
    """
    loaded = {}

    def __init__(self, fname, pos, z=0):
        self.flip_x = False
        self.default, self.animations = self.load(os.path.join('assets', 'animations', fname))
        self.playing = self.default
        super(Animation, self).__init__(pos, self.get_animation('default'), z=z)
        self.sprite.set_handler('on_animation_end', self.on_animation_end)

    def set_scenegraph(self, sg):
        if sg is None:
            self.sprite.pop_handlers()
            self.sprite.remove_handler('on_animation_end', self.on_animation_end)
        super(Animation, self).set_scenegraph(sg)

    def on_animation_end(self, *args):
        if self.sprite.image.frames[-1].duration is None:
            self.play('default')

    def set_flip(self, flip):
        if flip == self.flip_x:
            return
        self.play(self.playing, flip)

    def load(self, fname):
        try:
            default, animations = self.loaded[fname]
        except KeyError:
            pass

        from pyglet.image import Animation, AnimationFrame

        with open(fname) as f:
            self.doc = json.load(f)

        animations = {}
        default = None
        for name, a in self.doc.items():
            if name == 'default':
                if isinstance(a, unicode):
                    default = a
                    continue
                else:
                    default = 'default'
            frames = []
            for f in a['frames']:
                im = pyglet.resource.image(f['file']) 
                im.anchor_x, im.anchor_y = a.get('anchor', (0, 0))
                frames.append(
                    [im, a.get('frametime', 0.1)]
                )

            if not a.get('loop', False):
                if len(frames) == 1:
                    frames.append(frames[0])
                frames[-1][1] = 0

            animations[name] = Animation([AnimationFrame(*f) for f in frames])
        self.loaded[fname] = default, animations
        return default, animations

    def get_animation(self, name):
        if name == 'default':
            return self.animations[self.default]
        return self.animations[name]

    def play(self, name, flip=None):
        if name == 'default':
            name = self.default

        if name == self.playing and (flip is None or flip == self.flip_x):
            return
        if flip is not None:
            self.flip_x = flip
        anim = self.get_animation(name)
        if self.flip_x:
            anim = anim.get_transform(flip_x=True)
        self.playing = name
        self.sprite.image = anim


class AnimatedEffect(Animation):
    def on_animation_end(self, *args):
        self.scenegraph.remove(self)


class Depth(Node):
    def __init__(self, node, dz, pos=v(0, 0)):
        self.node = node
        self.dz = dz
        self.pos = v(pos)

    def get_position(self):
        return self._pos

    def set_position(self, pos):
        self._pos = pos
        self.node.pos = pos

    pos = property(get_position, set_position)

    @property
    def z(self):
        return self.node.z + self.dz

    def draw(self, camera):
        gl.glPushMatrix()
        gl.glTranslatef(self.pos.x, self.pos.y, self.dz)
        self.node.draw(camera)
        gl.glPopMatrix()


class GroundPlane(Node):
    z = -900

    def __init__(self, near_colour, far_colour, y=0):
        self.near_colour = list(near_colour)
        self.far_colour = list(far_colour)
        self.y = y

    def draw(self, camera):
        far = camera.far_plane()
        near = camera.near_plane()
        focus = camera.focus
        coords = ('v3f', [
            near.l, self.y, focus - camera.near,
            near.r, self.y, focus - camera.near,
            far.r, self.y, focus - camera.far,
            far.l, self.y, focus - camera.far,
        ])
        col = ('c4B', self.near_colour * 2 + self.far_colour * 2)
        pyglet.graphics.draw(4, gl.GL_QUADS, coords, col)


class SkyBox(Node):
    z = -901

    def __init__(self, horizon_colour, zenith_colour):
        self.horizon_colour = list(horizon_colour)
        self.zenith_colour = list(zenith_colour)

    def draw(self, camera):
        far = camera.far_plane()
        z = -camera.far + camera.focus
        coords = ('v3f', [
            far.l, 0, z,
            far.r, 0, z,
            far.r, far.t, z,
            far.l, far.t, z,
        ])
        col = ('c4B', self.horizon_colour * 2 + self.zenith_colour * 2)
        pyglet.graphics.draw(4, gl.GL_QUADS, coords, col)


class RectNode(Node):
    def __init__(self, rect, colour, z=0):
        self.rect = rect
        self.colour = colour
        self.z = z

    def draw(self, camera):
        gl.glColor4f(*self.colour)
        r = self.rect
        z = self.z
        coords = ('v3f', [
            r.l, r.b, z,
            r.r, r.b, z,
            r.r, r.t, z,
            r.l, r.t, z,
        ])
        pyglet.graphics.draw(4, gl.GL_QUADS, coords)
        gl.glColor4f(1, 1, 1, 1)


class Bullet(Node):
    z = -0.1
    trail_width = 2

    batch = pyglet.graphics.Batch()
    MAX_AGE = 0.6
    MAX_LENGTH = 500

    def __init__(self, segment):
        self.seg = segment
        self.t = None
        self.build()
    
    def build(self, age=0):
        p1, p2 = self.seg.points
        across = self.seg.axis * 0.5 * self.trail_width

        length = self.seg.length / self.MAX_LENGTH
        frac = (age / self.MAX_AGE)
        frac2 = frac * frac
        c1 = (1, 1, 1, max(0, 0.1 - frac2))
        c2 = (1, 1, 1, min(1, length * self.MAX_AGE  - frac2))

        bl = p1 - across
        br = p2 - across
        tr = p2 + across
        tl = p1 + across

        self.vl = pyglet.graphics.vertex_list(4,
            ('v2f', list(chain(bl, br, tr, tl))),
            ('c4f', list(chain(c1, c2, c2, c1))),
        )

    def update(self, age):
        self.vl.delete()
        self.build(age)

    def draw(self, camera):
        if self.t is None:
            self.t = self.scenegraph.t
        else:
            age = self.scenegraph.t - self.t
            if age > self.MAX_AGE:
                self.scenegraph.remove(self)
                return
            else:
                self.update(age)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        self.vl.draw(gl.GL_QUADS)


class DebugGeometryNode(CompoundNode):
    z = 10
    def __init__(self, physics, colour=(1, 0, 1, 0.5)):
        self.physics = physics
        children = []
        for r in physics.static_geometry:
            children.append(RectNode(r, colour))
        super(DebugGeometryNode, self).__init__(children=children)

    def draw(self, camera):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        super(DebugGeometryNode, self).draw(camera)
        for d in self.physics.dynamic:
            RectNode(d.get_rect(), (0, 1, 0, 0.5)).draw(camera)


class Fill(Node):
    z = -1000

    def __init__(self, colour):
        self.colour = colour

    def draw(self, camera):
        gl.glClearColor(*self.colour)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)


class Scenegraph(object):
    def __init__(self):
        self.objects = set()
        self.t = 0

    def update(self, dt):
        self.t += dt

    def add(self, obj):
        obj.set_scenegraph(self)
        self.objects.add(obj)

    def remove(self, obj):
        obj.set_scenegraph(None)
        self.objects.remove(obj)

    def draw(self, camera):
        camera.setup_matrixes()
        obs = list(self.objects)
        obs.sort(key=lambda x: x.z)
        for o in obs:
            o.draw(camera)

    def on_key_press(self, symbol, modifier):
        for o in self.objects:
            if hasattr(o, 'on_key_press'):
                o.on_key_press(symbol, modifier)


if __name__ == '__main__':
    WIDTH = 800
    HEIGHT = 600
    w = pyglet.window.Window(width=800, height=600)
    s = Scenegraph()
#    s.add(Fill((1.0, 1.0, 1.0, 1.0)))
#    s.add(Wheels((91, 0)))
#    s.add(Wheels((992 - 236, 0)))
#    s.add(StaticImage((0, 53), 'car-interior.png'))
#    s.add(StaticImage((90, 115), 'pc-standing.png'))
#    s.add(StaticImage((600, 115), 'lawman-standing.png'))
#    s.add(StaticImage((300, 115), 'table.png'))
#    s.add(StaticImage((500, 115), 'crate.png'))
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

    s.add(Locomotive(pos=(0, 0)))
    camera = Camera((200.0, 200.0), WIDTH, HEIGHT)

    @w.event
    def on_draw():
        s.draw(camera)

    def update(dt):
        camera.offset += v(100, 0) * dt
        s.update(dt)

    pyglet.clock.schedule_interval(update, 1/60.0)
    pyglet.app.run()
