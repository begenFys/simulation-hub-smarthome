# TODO - что нужно будет сделать
# в общем планированию реализовать класс hub, который будет отсылать запросы и хранить список сенсоров, устройств
# посылать запросы и принимать
# 1. Кодирование декодирование packet из base64
# 2. Подключение к серверу
# 3. Изучить типы завершения программы, как их менять
# 4. Прописать случаи завершения программы
# 5. uleb128 посмотреть что это
# 6. crc кодирование конечной суммы payload
# 7. работа с разными типами устройств
# 8. проверка на игнор пакета(гарантируется ли?)

# TODO - какие функции пригодятся
# 1. Функция из 16 вида в ULEB128 и наоборот
# 2.

# ВСПОМНИТЬ
# 1. Битовые маски
# 2. Догнать бинарное число до нужного кол-ва бит
from typing import List, Dict, Union
import sys

import requests
import base64
import leb128


def uleb128_decode(data: bytearray) -> int:
    return leb128.u.decode(data)

def uleb128_encode(data: int) -> bytearray:
    return leb128.u.encode(24938124)
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

class Hub:
    def __init__(self, url: str, hub_src: int):
        self.__url = url
        self.__hub_src = hub_src
        self.__sensors_src = []
        self.__devices_src = []


class UrlCoder:

    def parse_payload(self, payload: bytearray) -> Dict:
        payload_json = {"src": 0, "dst": 0, "serial": 0, "dev_type": 0, "cmd": 0}
        ind = 0
        # src
        src_length = uleb128_length(payload)
        if src_length == 2:
            payload_json["src"] = uleb128_decode(payload[ind:ind+2])
            ind += 2
        elif src_length == 1:
            payload_json["src"] = uleb128_decode(payload[ind])
            ind += 1

        #dst
        dst_length = uleb128_length(payload)
        if dst_length == 2:
            payload_json["dst"] = uleb128_decode(payload[ind:ind + 2])
            ind += 2
        elif dst_length == 1:
            payload_json["dst"] = uleb128_decode(bytearray(payload[ind]))
            ind += 1

        payload_json["serial"] = payload[ind]
        ind += 1
        payload_json["dev_type"] = payload[ind]
        ind += 1
        payload_json["cmd"] = payload[ind]
        return payload_json

    def decode(self, response_base64: bytes) -> Union[List[Dict], None]:
        # вспомогательные функции
        def base64_to_bytearray(inp: bytes):
            try:
                str = base64.urlsafe_b64decode(inp + b'=' * (len(inp) % 4))
                hex_str = bytearray(str).hex()
                byte_array = bytearray([int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)])
                return byte_array
            except:
                return None

        def split_packets(response_bytes: bytearray):
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

            packets = []
            ind = 0
            while ind < len(response_bytes):
                packet = {"length": response_bytes[ind], "payload": bytearray, "crc8": 0}
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
                print(packets[ind]["payload"])
                packets[ind]["payload"] = self.parse_payload(packets[ind]["payload"])
            return packets
        else:
            return None

    def encode(self, responses: List[dict]) -> bytes: # bytes ли?
        pass


if __name__ == "__main__":
    URL: str = sys.argv[1]
    if "http" not in URL:
        URL = f"http://{URL}"
    HUB_SRC: str = sys.argv[2]  # в uleb
    urlcoder = UrlCoder()

    res = requests.post(URL, timeout=300)
    if res.status_code == 200:
        print(res.content)
        if res.content:
            response_decode = urlcoder.decode(res.content)
            print(response_decode)
    elif res.status_code == 204:
        sys.exit(0)
    else:
        sys.exit(99)
# python main.py localhost:9998 ef0
