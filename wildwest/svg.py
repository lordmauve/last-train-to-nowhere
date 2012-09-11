from xml.etree import ElementTree
from geom import Rect

SOURCES = {
    'crate': '../assets/geometry/crate.svg',
    'mailcar': '../assets/geometry/mailcar.svg',
}


def parse(filename):
    with open(filename, 'r') as f:
        tree = ElementTree.parse(f)
        return tree


def images(tree):
    for node in tree.findall('.//{http://www.w3.org/2000/svg}image'):
        x = node.attrib.get('x')
        y = node.attrib.get('x')
        width = node.attrib.get('width')
        height = node.attrib.get('height')
        print x, y, height, width


def rectangles(tree):
    rect = []
    for node in tree.findall('.//{http://www.w3.org/2000/svg}rect'):
        x = node.attrib.get('x')
        y = node.attrib.get('x')
        width = node.attrib.get('width')
        height = node.attrib.get('height')
        rect += Rect.from_blwh(x, y, width, height)
    return rect


def get_geometry(obj_type):
    tree = parse(SOURCES[obj_type])
    # images(tree)
    return rectangles(tree)


if __name__ == '__main__':
    print get_geometry('mailcar')
