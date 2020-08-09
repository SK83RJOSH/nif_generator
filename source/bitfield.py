from enum import IntEnum
import types


class AlphaFunction(IntEnum):
    """Describes alpha blend modes for NiAlphaProperty."""

    ONE = 0
    ZERO = 1
    SRC_COLOR = 2
    INV_SRC_COLOR = 3
    DEST_COLOR = 4
    INV_DEST_COLOR = 5
    SRC_ALPHA = 6
    INV_SRC_ALPHA = 7
    DEST_ALPHA = 8
    INV_DEST_ALPHA = 9
    SRC_ALPHA_SATURATE = 10


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
        print("before:", instance.value, bin(instance.value))
        instance.value = instance.value & ~self.mask
        instance.value |= (value << self.pos) & self.mask
        print("after:", instance.value, bin(instance.value))


class BasicBitfield(int):
    value: int = 0
    alpha_blend = BitfieldMember(0, 1, 0x0001, int)
    src_blend = BitfieldMember(1, 4, 0x001E, AlphaFunction)

    def __init__(self):
        self.value = 0
        self.alpha_blend = 1
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
print("src_blend", temp.src_blend, temp.value, bin(temp.value))
temp.src_blend = AlphaFunction.INV_DEST_ALPHA
print("src_blend", temp.src_blend, temp.value, bin(temp.value))
# print("src_blend", temp.src_blend, temp.value, bin(temp.value))
