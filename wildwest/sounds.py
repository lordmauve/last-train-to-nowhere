from pyglet import media
from pkg_resources import resource_filename



def load_sound(filename):
    fname = resource_filename(__name__, 'assets/sounds/%s' % filename)
    return media.StaticSource(media.load(fname))


GUNSHOT = load_sound('gunshot.wav')
PICKUP = load_sound('pickup.wav')
THUD = load_sound('thud.wav')
GALLOP = load_sound('gallop.wav')


if not media.have_avbin:
    print "You're missing out on the music! You need to install AVBin."
else:
    music = media.Player()
    fname = resource_filename(__name__, 'assets/music/oh_hi_oleandro.mp3')
    music.queue(media.load(fname))
    music.eos_action = media.Player.EOS_LOOP
    music.play()


class Channel(object):
    def __init__(self):
        pass

    def play(self, sound):
        player = media.ManagedSoundPlayer()
        player.queue(sound)
        player.play()
