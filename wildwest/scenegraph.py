import pyglet
from pyglet import gl

pyglet.resource.path += ['../assets/sprites']
pyglet.resource.reindex()


class Camera(object):
    """A camera object."""
    def __init__(self, offset):
        self.offset = offset

    def setup_matrixes(self, screen_w, screen_h):
        x, y = self.offset
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        near = 1.0
        far = 10000.0
        l = -0.5 * screen_w / (10 - near)
        r = -l
        b = -0.5 * screen_h / (10 - near)
        t = -b
        gl.glFrustum(l, r, b, t, near, far)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glTranslatef(-x, -y, -10)



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


class Fill(Node):
    z = -1000

    def __init__(self, colour):
        self.colour = colour

    def draw(self, camera):
        gl.glClearColor(*self.colour)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)


class Scenegraph(object):
    def __init__(self, screen_w, screen_h):
        self.objects = []
        self.screen_w = screen_w
        self.screen_h = screen_h

    def add(self, obj):
        obj.scenegraph = self
        self.objects.append(obj)

    def remove(self, obj):
        self.objects.remove(obj)

    def draw(self, camera):
        camera.setup_matrixes(
            self.screen_w,
            self.screen_h
        )
        self.objects.sort(key=lambda x: x.z)
        for o in self.objects:
            o.draw(camera)


if __name__ == '__main__':
    WIDTH = 800
    HEIGHT = 600
    w = pyglet.window.Window(width=800, height=600)
    s = Scenegraph(WIDTH, HEIGHT)
    s.add(Fill((1.0, 1.0, 1.0, 1.0)))
    s.add(StaticImage((10, 70), 'car-interior.png'))
    s.add(StaticImage((90, 167), 'pc-standing.png'))
    s.add(StaticImage((600, 167), 'lawman-standing.png'))
    s.add(StaticImage((300, 222), 'table.png'))
    s.add(StaticImage((500, 197), 'crate.png'))

    camera = Camera((400.0, 300.0))

    @w.event
    def on_draw():
        s.draw(camera)

    pyglet.app.run()
