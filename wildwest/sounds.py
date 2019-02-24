from pyglet import media
from pkg_resources import resource_filename



def load_sound(filename):
    fname = resource_filename(__name__, 'assets/sounds/%s' % filename)
    return media.StaticSource(media.load(fname))


GUNSHOT = load_sound('gunshot.wav')
PICKUP = load_sound('pickup.wav')
THUD = load_sound('thud.wav')
GALLOP = load_sound('gallop.wav')


def start_music():
    music = media.Player()
    fname = resource_filename(__name__, 'assets/music/oh_hi_oleandro.mp3')
    music.queue(media.load(fname))
    music.on_eos = start_music
    music.play()


if not media.have_avbin:
    print("You're missing out on the music! You need to install AVBin.")
else:
    start_music()


class Channel(object):
    def __init__(self):
        pass

    def play(self, sound):
        player = media.Player()
        player.queue(sound)
        player.play()
