class BitfieldMember(object):

    def __init__(self, value=0, pos=0, width=0, mask=0, return_type=bool):
        self.value = value
        self.pos = pos
        self.mask = mask
        self.width = width
        self.return_type = return_type

    # see https://github.com/niftools/nifxml/issues/76 for reference
    def __get__(self, instance, owner):
        return self.return_type((instance.value & self.mask) >> self.pos)

    def __set__(self, instance, value):
        instance.value = (instance.value & self.mask) | (value << self.pos)


class BasicBitfield(int):
    value: int = 0
    alpha_blend = BitfieldMember(0, 0, 1, 0x0001)
    src_blend = BitfieldMember(0, 1, 4, 0x001E)


temp = BasicBitfield()
# temp.value = 0
print("alpha_blend", temp.alpha_blend, temp.value, bin(temp.value))
temp.alpha_blend = 1
print("alpha_blend", temp.alpha_blend, temp.value, bin(temp.value))

print("src_blend", temp.src_blend, temp.value, bin(temp.value))
temp.src_blend = 3
print("src_blend", temp.src_blend, temp.value, bin(temp.value))
