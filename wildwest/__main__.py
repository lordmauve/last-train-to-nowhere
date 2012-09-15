from optparse import OptionParser
import pyglet

from .game import Game, PlayGameState


def main():
    parser = OptionParser()
    parser.add_option('--debug', action='store_true', help='Debug collision geometries')
    parser.add_option('-l', '--level', type='int', help='Start at this level', default=1)
    options, args = parser.parse_args()

    PlayGameState.level = options.level
    g = Game()
    if options.debug:
        g.set_debug()
    pyglet.app.run()



if __name__ == '__main__':
    main()

