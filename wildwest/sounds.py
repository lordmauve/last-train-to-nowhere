import os
from pyglet import media


def load_sound(filename):
    path = os.path.join('assets', 'sounds', filename)
    return media.StaticSource(media.load(path))


GUNSHOT = load_sound('gunshot.wav')
PICKUP = load_sound('pickup.wav')
THUD = load_sound('thud.wav')


music = media.Player()
music.queue(media.load(os.path.join('assets', 'music', 'oh_hi_oleandro.mp3')))
music.play()


class Channel(object):
    def __init__(self):
        pass

    def play(self, sound):
        player = media.ManagedSoundPlayer()
        player.queue(sound)
        player.play()
