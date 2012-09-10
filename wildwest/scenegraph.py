import math
import pyglet
from pyglet import gl

from geom import Rect, v


pyglet.resource.path += [
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
    def __init__(self, children=(), pos=(0, 0)):
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
        assert isinstance(c, Node)
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


class AnimatedNode(Node):
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


class StaticImage(AnimatedNode):
    def __init__(self, pos, img, z=0):
        im = pyglet.resource.image(img)
        super(StaticImage, self).__init__(pos, im, z)


class Wheels(Node):
    z = -1

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


class Depth(Node):
    def __init__(self, node, dz):
        self.node = node
        self.dz = dz

    @property
    def z(self):
        return self.node.z + self.dz

    def draw(self, camera):
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, self.dz)
        self.node.draw(camera)
        gl.glPopMatrix()


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

        wheels = CompoundNode([
            LocomotiveWheel((303 + 82, 82)),
            LocomotiveWheel((303 + 180 + 82, 82))
        ])

        # Link the same object into the scenegraph twice! Ooo-err...
        self.add_child(wheels)
        self.add_child(Depth(wheels, -70))

        self.add_child(WheelBar((303 + 82, 82)))


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


class RailTrack(Node):
    z = -1
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


class Fill(Node):
    z = -1000

    def __init__(self, colour):
        self.colour = colour

    def draw(self, camera):
        gl.glClearColor(*self.colour)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)


class Scenegraph(object):
    def __init__(self):
        self.objects = []
        self.t = 0

    def update(self, dt):
        self.t += dt

    def add(self, obj):
        obj.set_scenegraph(self)
        self.objects.append(obj)

    def remove(self, obj):
        obj.set_scenegraph(None)
        self.objects.remove(obj)

    def draw(self, camera):
        camera.setup_matrixes()
        self.objects.sort(key=lambda x: x.z)
        for o in self.objects:
            o.draw(camera)


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
