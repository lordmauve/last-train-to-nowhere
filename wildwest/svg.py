from xml.etree import ElementTree
from geom import Rect


def parse(filename):
    with open(filename, 'r') as f:
        tree = ElementTree.parse(f)
        return tree


def images(tree):
    images = []
    doch = float(tree.getroot().get('height'))
    for node in tree.findall('.//{http://www.w3.org/2000/svg}image'):
        file = node.get('xlink:href')
        r = get_rect(node, doch)
        images.append((file, r))
    return images


def round_to_int(v):
    return int(float(v) + 0.5)


def get_rect(node, doch):
    x = round_to_int(node.get('x'))
    width = round_to_int(node.get('width'))

    # Load and transform y
    y = float(node.get('y'))
    height = float(node.get('height'))
    y = round_to_int(doch - height - y)
    height = round_to_int(height)

    return Rect.from_blwh((x, y), width, height)


def rectangles(tree):
    rect = []
    doch = float(tree.getroot().get('height'))
    for node in tree.findall('.//{http://www.w3.org/2000/svg}rect'):
        r = get_rect(node, doch)
#        print node.get('id'), r
        rect.append(r)
    return rect


def load_geometry(obj_type):
    source = 'assets/geometry/%s.svg' % obj_type
    tree = parse(source)
    return rectangles(tree)


if __name__ == '__main__':
    print load_geometry('mailcar')
