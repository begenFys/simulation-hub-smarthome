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
import sys
from typing import List

import requests
import urllib.parse
import base64


#

class Hub:
    def __init__(self, url: str, hub_src: int):
        self.__url = url
        self.__hub_src = hub_src
        self.__sensors_src = []
        self.__devices_src = []


class UrlCoder:
    def base64_to_bytearray(self, inp: bytes):
        try:
            str = base64.urlsafe_b64decode(inp + b'=' * (len(inp) % 4))
            hex_str = bytearray(str).hex()
            byte_array = bytearray([int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)])
            return byte_array
        except:
            return None

    def calculate_crc8(self, data: bytearray):
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

    def split_packets(self, response_bytes: bytearray):
        packets = []
        ind = 0
        while ind < len(response_bytes):
            packet = {"length": response_bytes[ind], "payload": bytearray, "crc8": 0}
            ind += 1
            packet["payload"] = response_bytes[ind:ind + packet["length"]]
            ind += packet["length"]
            packet["crc8"] = response_bytes[ind]

            if packet["crc8"] == self.calculate_crc8(packet["payload"]): # игнор пакет, если контрольная не совпадает
                packets.append(packet)
            ind += 1
        return packets

    def parse_payload(self, payload: bytearray):
        pass

    def decode(self, response_base64: bytes):
        response_bytes = self.base64_to_bytearray(response_base64)
        if response_bytes:
            packets = self.split_packets(response_bytes)
            return packets
        else:
            return None

    def encode(self, responses: List[dict]):
        pass


if __name__ == "__main__":
    URL: str = sys.argv[1]
    if "http" not in URL:
        URL = f"http://{URL}"
    HUB_SRC: str = sys.argv[2]  # в uleb
    urlcoder = UrlCoder()

    res = requests.post(URL)
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
