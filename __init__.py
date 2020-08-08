import logging
import time # for timing stuff
import re
import types
import os
import sys
import collections
import xml.etree.ElementTree as ET
import os, filters
from distutils.dir_util import copy_tree
from typing import Dict, List
from jinja2 import Environment, PackageLoader
from xml.etree import ElementTree
from html import unescape

import naming_conventions as convention

env = Environment(
    loader=PackageLoader('__init__', 'templates'),
    keep_trailing_newline=True,
)

env.filters["bitflag"] = filters.bitflag
env.filters["escape_backslashes"] = filters.escape_backslashes
env.filters["hex_string"] = filters.hex_string
env.filters["enum_name"] = filters.enum_name
env.filters["field_name"] = filters.field_name
env.filters["to_basic_type"] = filters.to_basic_type

basics: List[str] = []

def write_file(filename: str, contents: str):
    dir = os.path.dirname(filename)
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(contents)

class XmlParser:
    struct_types = ("compound", "niobject", "struct")
    bitstruct_types = ("bitfield", "bitflags", "bitstruct")

    def __init__(self):
        """Set up the xml parser."""

        # initialize dictionaries
        # map each supported version string to a version number
        versions = {}
        # map each supported game to a list of header version numbers
        games = {}
        # note: block versions are stored in the _games attribute of the struct class

        # elements for creating new classes
        self.class_name = None
        self.class_dict = None
        self.base_class = ()
        #
        # self.basic_classes = []
        # # these have to be read as basic classes
        # self.compound_classes = []

        # elements for versions
        self.version_string = None

        # ordered (!) list of tuples ({tokens}, (target_attribs)) for each <token>
        self.tokens = []
        self.versions = [ ([], ("versions", "until", "since")), ]

        # maps each type to its generated py file's relative path
        self.path_dict = {}
        # maps each type to its member tag type
        self.tag_dict = {}

    def generate_module_paths(self, root):
        """preprocessing - generate module paths for imports relative to the output dir"""
        for child in root:
            # only check stuff that has a name - ignore version tags
            if child.tag not in ("version", "module", "token"):
                class_name = convention.name_class(child.attrib["name"])
                out_segments = [child.tag, ]
                if child.tag == "niobject":
                    out_segments.append(child.attrib["module"])
                out_segments.append(class_name)
                # store the final relative module path for this class
                self.path_dict[class_name] = os.path.join(*out_segments)
                self.tag_dict[class_name] = child.tag
        # print(self.path_dict)

    def load_xml(self, xml_file):
        """Loads an XML (can be filepath or open file) and does all parsing
        Goes over all children of the root node and calls the appropriate function depending on type of the child"""
        # try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        self.generate_module_paths(root)

        for child in root:
            try:
                if child.tag in self.struct_types:
                    # StructWriter(child)
                    self.read_struct(child)
                # elif child.tag in self.bitstruct_types:
                #     self.read_bitstruct(child)
                # elif child.tag == "basic":
                #     self.read_basic(child)
                # elif child.tag == "alias":
                #     self.read_alias(child)
                elif child.tag == "enum":
                    self.write_enum(child)
                elif child.tag == "bitfield":
                    self.write_bitfield(child)
                elif child.tag == "bitflags":
                    self.write_bitflags(child)
                # elif child.tag == "module":
                #     self.read_module(child)
                # elif child.tag == "version":
                #     self.read_version(child)
                elif child.tag == "token":
                    self.read_token(child)
            except Exception as err:
                logging.error(err)

    # the following constructs do not create classes
    def read_token(self, token):
        """Reads an xml <token> block and stores it in the tokens list"""
        self.tokens.append(([(sub_token.attrib["token"], sub_token.attrib["string"])
                            for sub_token in token],
                            token.attrib["attrs"].split(" ")))
        
    def read_version(self, version):
        """Reads an xml <version> block and stores it in the versions list"""
        # todo [versions] this ignores the user vers!
        # versions must be in reverse order so don't append but insert at beginning
        if "id" in version.attrib:
            self.versions[0][0].insert( 0, (version.attrib["id"], version.attrib["num"]) )
        # add to supported versions
        self.version_string = version.attrib["num"]
        self.cls.versions[self.version_string] = self.cls.version_number(self.version_string)
        self.update_gamesdict(self.cls.games, version.text)
        self.version_string = None
    
    def read_module(self, module):
        """Reads a xml <module> block"""
        # no children, not interesting for now
        pass

    def read_basic(self, basic):
        """Maps to a type defined in self.cls"""
        self.class_name = basic.attrib["name"]
        # Each basic type corresponds to a type defined in C{self.cls}.
        # The link between basic types and C{self.cls} types is done via the name of the class.
        basic_class = getattr(self.cls, self.class_name)
        # check the class variables
        is_template = self.is_generic(basic.attrib)
        # if basic_class._is_template != is_template:
        #     raise XmlError( 'class %s should have _is_template = %s' % (self.class_name, is_template))

        # link class cls.<class_name> to basic_class
        setattr(self.cls, self.class_name, basic_class)
    
    # the following constructs create classes
    def read_bitstruct(self, bitstruct):
        """Create a bitstruct class"""
        attrs = self.replace_tokens(bitstruct.attrib)
        self.base_class = BitStructBase
        self.update_class_dict(attrs, bitstruct.text)
        try:
            numbytes = int(attrs["numbytes"])
        except KeyError:
            # niftools style: storage attribute
            numbytes = getattr(self.cls, attrs["storage"]).get_size()
        self.class_dict["_attrs"] = []
        self.class_dict["_numbytes"] = numbytes
        for member in bitstruct:
            attrs = self.replace_tokens(member.attrib)
            if member.tag == "bits":
                # eg. <bits name="Has Folder Records" numbits="1" default="1" />
                # mandatory parameters
                bit_attrs = attrs
            elif member.tag == "option":
                # niftools compatibility, we have a bitflags field
                # so convert value into numbits
                # first, calculate current bit position
                bitpos = sum(bitattr.numbits for bitattr in self.class_dict["_attrs"])
                # avoid crash
                if "value" in attrs:
                    # check if extra bits must be inserted
                    numextrabits = int(attrs["value"]) - bitpos
                    if numextrabits < 0:
                        raise XmlError("values of bitflags must be increasing")
                    if numextrabits > 0:
                        reserved = dict(name="Reserved Bits %i"% len(self.class_dict["_attrs"]), numbits=numextrabits)
                        self.class_dict["_attrs"].append( BitStructAttribute( self.cls, reserved))
                # add the actual attribute
                bit_attrs = dict(name=attrs["name"], numbits=1)
            # new nif xml    
            elif member.tag == "member":
                bit_attrs = dict(name=attrs["name"], numbits=attrs["width"])
            else:
                raise XmlError("only bits tags allowed in struct type declaration")
            
            self.class_dict["_attrs"].append( BitStructAttribute(self.cls, bit_attrs) )
            self.update_doc(self.class_dict["_attrs"][-1].doc, member.text)

        self.create_class(bitstruct.tag)

    def clean_comment_str(self, comment_str, indent=""):
        """Reformats an XML comment string into multi-line a python style comment block"""
        if not comment_str:
            return ""
        lines = [f"\n{indent}# {line.strip()}" for line in comment_str.strip().split("\n")]
        return "\n" + "".join(lines)

    def read_struct(self, struct):
        """Create a struct class"""
        attrs = self.replace_tokens(struct.attrib)
        # self.update_class_dict(attrs, struct.text)
        # struct types can be organized in a hierarchy
        # if inherit attribute is defined, look for corresponding base block
        class_name = convention.name_class(attrs.get("name"))
        class_basename = attrs.get("inherit")
        class_debug_str = self.clean_comment_str(struct.text)
        if class_basename:
            # avoid turning None into 'None' if class doesn't inherit
            class_basename = convention.name_class(class_basename)
            logging.debug(f"Struct {class_name} is based on {class_basename}")

        # generate paths
        # get the module path from the path of the file
        out_file = os.path.join(os.getcwd(), "generated", self.path_dict[class_name]+".py")
        out_dir = os.path.dirname(out_file)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        out_file = os.path.join(out_dir, class_name+".py")

        # list of all classes that have to be imported
        imports = []

        # lookup members
        local_lower_lookup = {}

        field_unions_dict = collections.OrderedDict()
        for field in struct:
            field_attrs = self.replace_tokens(field.attrib)
            if field.tag in ("add", "field"):
                field_name = convention.name_attribute(field_attrs["name"])
                local_lower_lookup[field_attrs["name"]] = "self."+field_name
                if field_name not in field_unions_dict:
                    field_unions_dict[field_name] = []
                else:
                    # field exists and we add to it, so we have an union and must import typing module
                    imports.append("typing")
                field_unions_dict[field_name].append(field)

        # import parent class
        if class_basename:
            imports.append(class_basename)
        # import classes used in the fields
        for field in struct:
            if field.tag in ("add", "field"):
                field_type = convention.name_class(field.attrib["type"])
                if field_type not in imports:
                    imports.append(field_type)

        # write to python file
        with open(out_file, "w") as f:
            for class_import in imports:
                if class_import in self.path_dict:
                    f.write(f"from .{self.path_dict[class_import]} import {class_import}\n")
                else:
                    f.write(f"import {class_import}\n")

            if imports:
                f.write("\n\n")
            if class_basename:
                f.write(f"class {class_name}({class_basename}):")
            else:
                f.write(f"class {class_name}:")
            if class_debug_str:
                f.write(class_debug_str)

            # check all fields/members in this class and write them as fields
            for field_name, union_members in field_unions_dict.items():
                field_types = []
                for field in union_members:
                    field_attrs = self.replace_tokens(field.attrib)
                    field_type = convention.name_class(field_attrs["type"])
                    field_types.append(field_type)
                    field_default = field_attrs.get("default")
                    field_debug_str = self.clean_comment_str(field.text, indent="\t")

                    if field_debug_str.strip():
                        f.write(field_debug_str)
                if len(union_members) > 1:
                    field_types_str = f"typing.Union[{', '.join(field_types)}]"
                else:
                    field_types_str = field_type

                # write the field type
                # arrays
                if field_attrs.get("arr1"):
                    f.write(f"\n\t{field_name}: List[{field_types_str}]")
                # plain
                else:
                    f.write(f"\n\t{field_name}: {field_types_str}")

                # write the field's default, if it exists
                if field_default:
                    # we have to check if the default is an enum default value, in which case it has to be a member of that enum
                    if self.tag_dict[field_type] == "enum":
                        field_default = field_type+"."+field_default
                    f.write(f" = {field_default}")

                # todo - handle several defaults? maybe save as docstring
                # load defaults for this <field>
                # for default in field:
                #     if default.tag != "default":
                #         raise AttributeError("struct children's children must be 'default' tag")

            # write the load() method
            for method_type in ("load", "save"):
                # check all fields/members in this class and write them as fields
                f.write(f"\n\n\tdef {method_type}(self, stream):")
                # classes that this class inherits from have to be read first
                if class_basename:
                    f.write(f"\n\t\tsuper().{method_type}(stream)")

                for field in struct:
                    field_attrs = self.replace_tokens(field.attrib)
                    if field.tag in ("add", "field"):
                        field_name = convention.name_attribute(field_attrs["name"])
                        field_type = convention.name_class(field_attrs["type"])
                        # todo - decide if basic or compound
                        # assume compound

                        for att in ("cond", "vercond", "arr1", "arr2"):
                            if att in field_attrs:
                                val = field_attrs[att]
                                for k, v in local_lower_lookup.items():
                                    val = val.replace(k, v)
                                field_attrs[att] = val

                        conditionals = []
                        ver1 = field_attrs.get("ver1")
                        ver2 = field_attrs.get("ver2")
                        vercond = field_attrs.get("vercond")
                        cond = field_attrs.get("cond")
                        if ver1:
                            conditionals.append(f"(version < {ver1})")
                        if ver2:
                            conditionals.append(f"(version < {ver2})")
                        if vercond:
                            conditionals.append(f"({vercond})")
                        if cond:
                            conditionals.append(f"({cond})")
                        if conditionals:
                            f.write(f"\n\t\tif {' and '.join(conditionals)}:")
                            indent = "\n\t\t\t"
                        else:
                            indent = "\n\t\t"
                        arr1 = field_attrs.get("arr1")
                        arr2 = field_attrs.get("arr2")
                        if arr1:
                            # todo - handle array 2
                            f.write(f"{indent}self.{field_name} = [{field_type}() for _ in range({arr1})]")
                            f.write(f"{indent}for item in self.{field_name}:")
                            f.write(f"{indent}\titem.{method_type}(stream)")

                        else:
                            f.write(f"{indent}self.{field_name} = {field_type}().{method_type}(stream)")


                    # # not found in current nifxml
                    # elif field.tag == "version":
                    #     # set the version string
                    #     self.version_string = attrs["num"]
                    #     self.cls.versions[self.version_string] = self.cls.version_number(self.version_string)
                    #     self.update_gamesdict(self.class_dict["_games"], field.text)
                    # else:
                    #     print("only add and version tags allowed in struct declaration")

    def write_bitflags(self, element: ElementTree.Element):
        class_name = convention.name_class(element.attrib['name'])
        out_file = os.path.join(os.getcwd(), "generated", self.path_dict[class_name]+".py")
        write_file(out_file, env.get_template('bitflags.py.jinja').render(bitflags=element))

    def write_bitfield(self, element: ElementTree.Element):
        class_name = convention.name_class(element.attrib['name'])
        out_file = os.path.join(os.getcwd(), "generated", self.path_dict[class_name]+".py")
        write_file(out_file, env.get_template('bitfield.py.jinja').render(bitfield=element))

    def write_enum(self, element: ElementTree.Element):
        class_name = convention.name_class(element.attrib['name'])
        out_file = os.path.join(os.getcwd(), "generated", self.path_dict[class_name]+".py")
        write_file(out_file, env.get_template('enum.py.jinja').render(enum=element))

    def read_alias(self, alias):
        """Create an alias class, ie. one that gives access to another class"""
        self.update_class_dict(alias.attrib, alias.text)
        typename = alias.attrib["type"]
        try:
            self.base_class = getattr(self.cls, typename)
        except AttributeError:
            raise XmlError("typo, or forward declaration of type %s" % typename)
        self.create_class(alias.tag)


    # the following are helper functions
    def is_generic(self, attr):
        # be backward compatible
        return (attr.get("generic") == "true") or (attr.get("istemplate") == "1")

    def update_gamesdict(self, gamesdict, ver_text):
        if ver_text:
            # update the gamesdict dictionary
            for gamestr in (g.strip() for g in ver_text.split(',')):
                if gamestr in gamesdict:
                    gamesdict[gamestr].append(self.cls.versions[self.version_string])
                else:
                    gamesdict[gamestr] = [self.cls.versions[self.version_string]]
        
    def update_class_dict(self, attrs, doc_text):
        """This initializes class_dict, sets the class name and doc text"""
        doc_text = doc_text.strip() if doc_text else ""
        self.class_name = attrs["name"]
        self.class_dict = {"__doc__": doc_text, "__module__": self.cls.__module__}

    def update_doc(self, doc, doc_text):
        if doc_text:
            doc += doc_text.strip()
            
    def replace_tokens(self, attr_dict):
        """Update attr_dict with content of tokens+versions list."""
        # replace versions after tokens because tokens include versions
        for tokens, target_attribs in self.tokens + self.versions:
            for target_attrib in target_attribs:
                if target_attrib in attr_dict:
                    expr_str = attr_dict[target_attrib]
                    for op_token, op_str in tokens:
                        expr_str = expr_str.replace(op_token, op_str)
                    attr_dict[target_attrib] = unescape(expr_str)
        # additional tokens that are not specified by nif.xml
        fixed_tokens = (("User Version", "user_version"), ("BS Header\\BS Version", "bs_header\\bs_version"), ("Version", "version"), ("\\", "."), ("#ARG#", "ARG"), ("#T#", "TEMPLATE") )
        for attrib, expr_str in attr_dict.items():
            for op_token, op_str in fixed_tokens:
                expr_str = expr_str.replace(op_token, op_str)
            attr_dict[attrib] = expr_str
        # onlyT & excludeT act as aliases for deprecated cond
        prefs = ( ("onlyT", ""), ("excludeT", "!") )
        for t, pref in prefs:
            if t in attr_dict:
                attr_dict["cond"] = pref+attr_dict[t]
                break
        return attr_dict


def run():
    logging.basicConfig(level=logging.DEBUG)
    # logging.warning('Watch out!')
    logging.info("Starting class generation")
    cwd = os.getcwd()
    xml_dir = os.path.join(cwd, "formats")
    for xml_file in os.listdir(xml_dir):
        if xml_file.lower().endswith(".xml"):
            # print(xml_file)
            xml_path = os.path.join(xml_dir, xml_file)
            xmlp = XmlParser()
            xmlp.load_xml(xml_path)

run()