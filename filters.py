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


def to_common_type(type: str) -> str:
    # Temporary, these would likely be patched via a preprocessor
    if type is not None:
        if type == 'ulittle32':
            return 'pyffi.object_models.common.ULittle32'
        if type == 'int':
            return 'pyffi.object_models.common.Int'
        if type == 'uint':
            return 'pyffi.object_models.common.UInt'
        if type == 'byte':
            return 'pyffi.object_models.common.UByte'
        if type == 'char':
            return 'pyffi.object_models.common.Char'
        if type == 'short':
            return 'pyffi.object_models.common.Short'
        if type == 'ushort':
            return 'pyffi.object_models.common.UShort'
        if type == 'float':
            return 'pyffi.object_models.common.Float'
        if type == 'BlockTypeIndex':
            return 'pyffi.object_models.common.UShort'
        if type == 'StringIndex':
            return 'pyffi.object_models.common.UInt'
        if type == 'SizedString':
            return 'pyffi.object_models.common.SizedString'

    return type
