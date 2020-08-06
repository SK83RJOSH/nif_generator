import os
import filters
from jinja2 import Environment, PackageLoader
from xml.etree import ElementTree

env = Environment(
    loader=PackageLoader('generator', 'templates'),
    keep_trailing_newline=True,
)

env.filters["bitflag"] = filters.bitflag
env.filters["escape_backslashes"] = filters.escape_backslashes
env.filters["hex_string"] = filters.hex_string
env.filters["enum_name"] = filters.enum_name
env.filters["field_name"] = filters.field_name
env.filters["to_common_type"] = filters.to_common_type


def write_file(filename: str, contents: str):
    dir = os.path.dirname(filename)
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(contents)


def write_enum(element: ElementTree.Element):
    print(element.attrib['name'])
    write_file(
        "output/enums/%s.py" % (element.attrib['name']),
        env.get_template('enum.py.jinja').render(enum=element)
    )


def write_bitflags(element: ElementTree.Element):
    print(element.attrib['name'])
    write_file(
        "output/bitflags/%s.py" % (element.attrib['name']),
        env.get_template('bitflags.py.jinja').render(bitflags=element)
    )


def write_bitfield(element: ElementTree.Element):
    print(element.attrib['name'])
    write_file(
        "output/bitfields/%s.py" % (element.attrib['name']),
        env.get_template('bitfield.py.jinja').render(bitfield=element)
    )


def write_templates():
    nif_xml = ElementTree.parse('nifxml/nif.xml')
    root = nif_xml.getroot()

    for enum in root.iter('enum'):
        write_enum(enum)

    for bitflags in root.iter('bitflags'):
        write_bitflags(bitflags)

    for bitfield in root.iter('bitfield'):
        write_bitfield(bitfield)


write_templates()
