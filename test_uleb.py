import leb128

print(leb128.u.decode(bytearray([0x01, 0xff])))