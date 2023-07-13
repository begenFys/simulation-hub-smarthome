import leb128

print(leb128.u.decode(bytearray([0x01, 0xff])))
print(leb128.u.encode(24938124).hex())

print(bin(int("0f", 16)))


def uleb128_length(data: bytearray):
    length = 0
    index = 0

    while True:
        byte = data[index]
        length += 1
        index += 1

        if byte & 0x80 == 0:
            break

    return length

data = bytearray([0xb3, 0x06, 0xff, 0x7f, 0x06, 0x06, 0x06, 0xb4, 0x9b, 0xfe, 0x80, 0x95, 0x51])  # Пример числа ULEB128
length = uleb128_length(data)
print(length)  # Выводит: 2