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


class AnimatedNode(Node):
    def __init__(self, pos, animation, z=0):
        self.z = z
        self.sprite = pyglet.sprite.Sprite(animation)
        self.pos = pos

    def get_position(self):
        return self.sprite.position

    def set_position(self, pos):
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
        obj.scenegraph = self
        self.objects.append(obj)

    def remove(self, obj):
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
    s.add(Fill((1.0, 1.0, 1.0, 1.0)))
    s.add(StaticImage((0, 53), 'car-interior.png'))
    s.add(StaticImage((90, 115), 'pc-standing.png'))
    s.add(StaticImage((600, 115), 'lawman-standing.png'))
    s.add(StaticImage((300, 115), 'table.png'))
    s.add(StaticImage((500, 115), 'crate.png'))
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

    def update(dt):
        camera.offset += v(100, 0) * dt
        s.update(dt)

    pyglet.clock.schedule_interval(update, 1/30.0)
    pyglet.app.run()
