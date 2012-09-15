import pyglet
from pyglet import gl
from pyglet import resource

from .geom import Rect, v
from .scenegraph import Node


class HUD(Node):
    z = 1000000

    @classmethod
    def load(cls):
        if hasattr(cls, 'images'):
            return
        cls.images = {
            'healthbar-full': resource.image('healthbar-full.png'),
            'healthbar-empty': resource.image('healthbar-empty.png'),
            'healthbar': resource.image('healthbar.png'),
            'ammo-revolver': resource.image('ammo-revolver.png'),
            'ammo-bullet': resource.image('ammo-bullet.png'),
            'ammo': resource.image('ammo.png'),
            'goldmeter': resource.image('goldmeter.png'),
            'goldmeterbar': resource.image('goldmeterbar.png'),
        }

    def __init__(self, player):
        self.load()
        self.player = player
        self.build()
        
    def build(self):
        """Build vertex lists for the health bar."""
        r = Rect.from_blwh((110, 10), 167, 23)

        self.batch = pyglet.graphics.Batch()
        hb_full = self.images['healthbar-full'].texture
        group = pyglet.sprite.SpriteGroup(
            hb_full,
            gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA
        )

        self._hb_vs = [
            r.l, r.b,
            r.r, r.b,
            r.r, r.t,
            r.l, r.t
        ]
        tcs = hb_full.tex_coords
        self._hb_tcs = (
            tcs[0:2] +
            tcs[3:5] +
            tcs[6:8] +
            tcs[9:11]
        )

        self._hb_texrect = Rect.from_points(tcs[0:2], tcs[6:8])
        hb_tcs = (
            tcs[0:2] +
            tcs[3:5] +
            tcs[6:8] +
            tcs[9:11]
        )
        self._hb_full = self.batch.add(4, gl.GL_QUADS, group,
            ('v2f', self._hb_vs),
            ('t2f', hb_tcs)
        )
        self._hb_rect = r

    def draw(self, camera):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        vp = camera.viewport()
        vp = vp.translate(v(-vp.l, -vp.b))

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(vp.l, vp.r, vp.b, vp.t, -1000, 1000)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        self.draw_health(vp)
        self.draw_gold(vp)

    def draw_health(self, vp):
        self.images['healthbar'].blit(vp.l + 10, 10)
        self.images['healthbar-empty'].blit(vp.l + 110, 10)

        frac = max(0, min(1, self.player.health / self.player.MAX_HEALTH))
        r = self._hb_rect.l + frac * self._hb_rect.w
        self._hb_full.vertices[2] = r
        self._hb_full.vertices[4] = r

        ur = self._hb_texrect.l + self._hb_texrect.w * frac
        self._hb_full.tex_coords[2] = ur
        self._hb_full.tex_coords[4] = ur
        self.batch.draw()

    def draw_gold(self, vp):
        gmw = self.images['goldmeter'].width
        x = vp.r - 10 - gmw
        self.images['goldmeter'].blit(x, 10)

        x -= 25 + self.player.gold * 25
        for i in range(self.player.gold):
            self.images['goldmeterbar'].blit(x, 10)
            x += 25
