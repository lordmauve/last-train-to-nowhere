from optparse import OptionParser
import pyglet

from .game import Game, PlayGameState


def main():
    parser = OptionParser()
    parser.add_option('--debug', action='store_true', help='Debug collision geometries')
    parser.add_option('--profile', action='store_true', help='Run profiler')
    parser.add_option('-l', '--level', type='int', help='Start at this level', default=None)
    options, args = parser.parse_args()

    g = Game()
    if options.level:
        PlayGameState.level = options.level
        g.restart(gamestate=PlayGameState)
    if options.debug:
        g.set_debug()

    if options.profile:
        import hotshot
        import hotshot.stats
        import atexit
        p = hotshot.Profile('profile.log')

        @atexit.register
        def print_stats(): 
            stats = hotshot.stats.load("profile.log")
            stats.strip_dirs()
            stats.sort_stats('time', 'calls')
            stats.print_stats()

        p.runcall(pyglet.app.run)
    else:
        pyglet.app.run()



if __name__ == '__main__':
    main()

