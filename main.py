# TODO - что нужно будет сделать
# в общем планированию реализовать класс hub, который будет отсылать запросы и хранить список сенсоров, устройств
# посылать запросы и принимать
# 1. Кодирование декодирование packet из base64 +
# 2. Подключение к серверу
# 3. Изучить типы завершения программы, как их менять +
# 4. Прописать случаи завершения программы
# 5. uleb128 посмотреть что это +
# 6. crc кодирование конечной суммы payload +
# 7. работа с разными типами устройств
# 8. проверка на игнор пакета(гарантируется ли?) +

# TODO - какие функции пригодятся
# 1. Функция из 16 вида в ULEB128 и наоборот +
# 2.

# ВСПОМНИТЬ
# 1. Битовые маски
# 2. Догнать бинарное число до нужного кол-ва бит
from typing import List, Dict, Union
import sys

import requests
import base64
import leb128

BROADCAST_DST: int = 0x3fff
# Не совсем логичный следующее действие, так как заглавные буквы используют для обозначения констант,
# а дальше мы будем PACKETS изменять, но это сделано чтобы было видно и понятно, так что не думаю что это критично.
# Главное я пояснил момент
PACKETS: List[bytearray] = []  # пакеты, которые мы будем потом оформлять в запрос


class CMD:  # чтобы в циферках не запутаться)
    WHOISHERE = 1
    IAMHERE = 2
    GETSTATUS = 3
    STATUS = 4
    SETSTATUS = 5


# работа с форматов uleb128
def uleb128_decode(data: bytearray) -> int:
    return leb128.u.decode(data)


def uleb128_encode(data: int) -> bytearray:
    return leb128.u.encode(data)


def uleb128_length(data: bytearray) -> int:
    length = 0
    index = 0
    while True:
        byte = data[index]
        length += 1
        index += 1
        if byte & 0x80 == 0:
            break

    return length


# считаем crc8
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


# преобразуем строк в нужный нам вид
def str_to_bytearray(data: str) -> bytearray:
    byte_array = bytearray()
    byte_array.append(len(data))
    byte_array.extend(data.encode())
    return byte_array


class UrlCoder:
    @staticmethod
    def parse_payload(payload: bytearray) -> Dict:
        payload_json = {"src": 0, "dst": 0, "serial": 0, "dev_type": 0, "cmd": 0}
        ind = 0
        # src
        src_length = uleb128_length(payload[ind:])
        payload_json["src"] = uleb128_decode(payload[ind:ind + src_length]) if src_length > 1 else payload[ind]
        ind += src_length

        # dst
        dst_length = uleb128_length(payload[ind:])
        payload_json["dst"] = uleb128_decode(payload[ind:ind + dst_length]) if dst_length > 1 else payload[ind]
        ind += dst_length

        payload_json["serial"] = payload[ind]
        ind += 1
        payload_json["dev_type"] = payload[ind]
        ind += 1
        payload_json["cmd"] = payload[ind]
        return payload_json

    @staticmethod
    def decode(response_base64: bytes) -> Union[List[Dict], None]:
        # вспомогательные функции
        def base64_to_bytearray(inp: bytes) -> Union[bytearray, None]:
            try:
                str = base64.urlsafe_b64decode(inp + b'=' * (len(inp) % 4))
                hex_str = bytearray(str).hex()
                byte_array = bytearray([int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)])
                return byte_array
            except:
                return None

        def split_packets(response_bytes: bytearray) -> List[Dict]:
            packets = []
            ind = 0
            while ind < len(response_bytes):
                packet = {"length": response_bytes[ind], "payload": bytearray(), "crc8": 0}
                ind += 1
                packet["payload"] = response_bytes[ind:ind + packet["length"]]
                ind += packet["length"]
                packet["crc8"] = response_bytes[ind]
                if packet["crc8"] == calculate_crc8(packet["payload"]):  # игнор пакет, если контрольная не совпадает
                    packets.append(packet)
                ind += 1
            return packets

        # основной код
        response_bytes = base64_to_bytearray(response_base64)
        if response_bytes:
            packets = split_packets(response_bytes)
            for ind in range(len(packets)):
                packets[ind]["payload"] = UrlCoder.parse_payload(packets[ind]["payload"])
            return packets
        else:
            return None

    @staticmethod
    def encode_payload(src: int, dst: int, serial: int, dev_type: int, cmd: int) -> bytearray:
        payload = bytearray()
        payload.extend(uleb128_encode(src))
        payload.extend(uleb128_encode(dst))
        payload.extend(uleb128_encode(serial))
        payload.append(dev_type)
        payload.append(cmd)

        return payload

    @staticmethod
    def encode_packet(payload: bytearray) -> bytearray:
        packet = bytearray()
        packet.append(len(payload))
        packet.extend(payload)
        packet.append(calculate_crc8(payload))
        return packet

    @staticmethod
    def encode(packets: List[bytearray]) -> bytes:
        response = bytearray()
        for packet in packets:
            response.extend(packet)
        return base64.urlsafe_b64encode(response)


class Hub:
    def __init__(self, src: int, dev_name: str) -> None:
        self.src = src
        self.__serial = 1
        self.dev_type = 1
        self.dev_name = dev_name

    @property
    def serial(self) -> int:
        self.__serial += 1
        return self.__serial - 1

    def WHOISHERE(self) -> bytearray:
        payload = UrlCoder.encode_payload(self.src, BROADCAST_DST, self.__serial, self.dev_type, CMD.WHOISHERE)

        cmd_body = bytearray()
        cmd_body.extend(str_to_bytearray(self.dev_name))
        payload.extend(cmd_body)

        packet = UrlCoder.encode_packet(payload)
        return packet


if __name__ == "__main__":
    URL: str = sys.argv[1]
    if "http" not in URL:
        URL = f"http://{URL}"
    HUB_SRC: int = int(sys.argv[2], 16)  # в uleb

    hub = Hub(HUB_SRC, "HUB01")
    PACKETS.append(hub.WHOISHERE())
    while PACKETS:
        response = UrlCoder.encode(PACKETS)
        res = requests.post(URL, data=response, timeout=300)
        PACKETS.clear()
        if res.status_code == 200:
            print(res.content)
            print(UrlCoder.decode(res.content))
        elif res.status_code == 204:
            sys.exit(0)
        else:
            sys.exit(99)



# python main.py localhost:9998 ef0
