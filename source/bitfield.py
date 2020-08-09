
from enum import IntEnum
import types

class AlphaFunction(IntEnum):
    """Describes alpha blend modes for NiAlphaProperty."""

    # def __new__(cls, value, doc=None):
    #     self = super().__new__(cls, value)
    #     self._value_ = value
    #
    #     if doc is not None:
    #         self.__doc__ = doc
    #
    #     return self

    ONE = 0x00000000#, "None"
    ZERO = 0x00000001#, "None"
    SRC_COLOR = 0x00000002#, "None"
    INV_SRC_COLOR = 0x00000003#, "None"
    DEST_COLOR = 0x00000004#, "None"
    INV_DEST_COLOR = 0x00000005#, "None"
    SRC_ALPHA = 0x00000006#, "None"
    INV_SRC_ALPHA = 0x00000007#, "None"
    DEST_ALPHA = 0x00000008#, "None"
    INV_DEST_ALPHA = 0x00000009#, "None"
    SRC_ALPHA_SATURATE = 0x0000000A#, "None"



class BitfieldMember(object):

    def __init__(self, pos=0, width=0, mask=0, return_type=bool):
        self.pos = pos
        self.mask = mask
        self.width = width
        self.return_type = return_type

    # see https://github.com/niftools/nifxml/issues/76 for reference
    def __get__(self, instance, owner):
        return self.return_type((instance.value & self.mask) >> self.pos)

    def __set__(self, instance, value):
        print(f"setting bitfield value {value}")
        instance.value = (instance.value & self.mask) | (value << self.pos)


class BasicBitfield(int):
    value: int = 0
    alpha_blend = BitfieldMember(0, 1, 0x0001, int)
    src_blend = BitfieldMember(1, 4, 0x001E, AlphaFunction)

    def __init__(self):
        self.value = 0
        self.alpha_blend = 0
        self.src_blend = AlphaFunction.SRC_ALPHA

    def __repr__(self):
        return self.__str__

    def __str__(self):
        CALLABLES = types.FunctionType, types.MethodType
        print([key for key, value in self.__dict__.items() if not isinstance(value, CALLABLES)])
        info = str(vars(self))
        return info

# AlphaFunction(1)
temp = BasicBitfield()
print(AlphaFunction.INV_DEST_ALPHA.value)
# # temp.value = 0
# print("alpha_blend", temp.alpha_blend, temp.value, bin(temp.value))
# temp.alpha_blend = 1
# print("alpha_blend", temp.alpha_blend, temp.value, bin(temp.value))
#
# print(temp)
# print("src_blend", temp.src_blend, temp.value, bin(temp.value))
# temp.src_blend = AlphaFunction.INV_DEST_ALPHA
# print("src_blend", temp.src_blend, temp.value, bin(temp.value))
