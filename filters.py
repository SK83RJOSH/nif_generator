import re


def bitflag(bit: str) -> str:
    if bit is not None:
        return "0x%08X" % (1 << int(bit))

    return bit


def escape_backslashes(text: str) -> str:
    if text is not None:
        return text.replace('\\', '\\\\')

    return text


def hex_string(number: str) -> str:
    if number is not None:
        return "0x%08X" % int(number, base=0)

    return number


def enum_name(text: str) -> str:
    # This could maybe use an upper(), but maybe we should leave the enum names as they are
    if text is not None:
        return re.sub('[^a-zA-Z0-9_]', '_', text)

    return text


def field_name(text: str) -> str:
    if text is not None:
        return re.sub('[^a-zA-Z0-9_]', '_', text).lower()

    return text


def to_basic_type(type: str) -> str:
    # Temporary, these would likely be patched via a preprocessor
    if type is not None:
        if type == 'ulittle32':
            return 'basics.ulittle32'
        if type == 'int':
            return 'basics.int'
        if type == 'uint':
            return 'basics.uint'
        if type == 'uint64':
            return 'basics.int64'
        if type == 'uint':
            return 'basics.uint64'
        if type == 'byte':
            return 'basics.byte'
        if type == 'char':
            return 'basics.char'
        if type == 'short':
            return 'basics.short'
        if type == 'ushort':
            return 'basics.ushort'
        if type == 'float':
            return 'basics.float'
        if type == 'BlockTypeIndex':
            return 'basics.BlockTypeIndex'
        if type == 'StringIndex':
            return 'basics.StringIndex'
        if type == 'StringOffset':
            return 'basics.StringOffset'
        if type == 'FileVersion':
            return 'basics.FileVersion'
        if type == 'NiFixedString':
            return 'basics.NiFixedString'
        if type == 'Ref':
            return 'basics.Ref'
        if type == 'Ptr':
            return 'basics.Ptr'

    return type
