import crc8
import base64


def base64_to_bytearray(inp: bytes, view: bool = False):
    try:
        string = base64.urlsafe_b64decode(inp + b'=' * (len(inp) % 4))
        hex_str = bytearray(string).hex()
        byte_array = bytearray([int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)])
        if view:
            hex_view = [hex_str[i:i + 2] for i in range(0, len(hex_str), 2)]
            print("hex_view:", hex_view)
            bin_view = " ".join([bin(int(byte, 16))[2:] for byte in hex_view])
            print("bin_view", bin_view)
        return byte_array
    except:
        return None


response_bytes = base64_to_bytearray(b"DAH_fwEBAQVIVUIwMeE", True)
print(response_bytes)

ind = 0


def calculate_crc8(data: bytearray):
    crc = 0x00  # Начальное значение CRC

    for byte in data:
        crc ^= byte  # Исключающее ИЛИ между текущим значением CRC и байтом данных
        for _ in range(8):
            if crc & 0x80:  # Проверка старшего бита CRC
                crc = (crc << 1) ^ 0x1d  # Сдвиг влево и XOR с полиномом 0x1d
            else:
                crc <<= 1  # Сдвиг влево
        crc &= 0xff  # Ограничение CRC до 8 бит

    return crc


while ind < len(response_bytes):
    packet_length = response_bytes[ind]
    packet = response_bytes[ind + 1:ind + packet_length + 1]
    ind += packet_length + 1
    sm_crc8 = response_bytes[ind]
    ind += 1

    print(packet_length, packet, sm_crc8, calculate_crc8(packet))
