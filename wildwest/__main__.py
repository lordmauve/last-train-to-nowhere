from optparse import OptionParser
import pyglet

from .game import Game


def main():
    parser = OptionParser()
    parser.add_option('--debug', action='store_true', help='Debug collision geometries')
    options, args = parser.parse_args()

    g = Game()
    if options.debug:
        g.set_debug()
    pyglet.app.run()



if __name__ == '__main__':
    main()

