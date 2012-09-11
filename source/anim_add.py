import os
import json
import shutil
from optparse import OptionParser
import pprint

parser = OptionParser()
parser.add_option('-f', '--file', help='Animation file to edit')
parser.add_option('-d', '--default', action='store_true', help='Set named animation as default')
parser.add_option('-D', '--delete', action='store_true', help='Remove named animation')
parser.add_option('-n', '--name', help='Animation name to update')
parser.add_option('-a', '--anchor', help='Anchor point')
parser.add_option('-l', '--loop', dest='loop', action='store_true', help='Loop animation')
parser.add_option('--no-loop', dest='loop', action='store_false', help='Do not loop animation')
parser.add_option('-t', '--frametime', help='Time per frame')

options, args = parser.parse_args()


try:
    with open(options.file) as f:
        doc = json.load(f)
except (IOError, TypeError):
    doc = {}


if options.delete:
    try:
        del(doc[options.name])
    except KeyError:
        pass
else:
    anew = {}
    if options.anchor:
        x, y = options.anchor.split(',')
        anew['anchor'] = int(x), int(y)

    if options.loop is not None:
        anew['loop'] = options.loop

    if options.frametime:
        anew['frametime'] = float(options.frametime)

    if args:
        anew['frames'] = [{'file': a} for a in args]

    doc.setdefault(options.name, {}).update(anew)

    if options.default:
        doc['default'] = options.name

if os.path.exists(options.file):
    shutil.copyfile(options.file, options.file + '.orig')

with open(options.file, 'w') as f:
    f.write(json.dumps(doc)) 

pprint.pprint(doc)
