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
    @staticmethod
    def encode(text: str):
        pass

    @staticmethod
    def decode(text: bytes):
        decoded_data = urllib.parse.unquote(text)
        print(decoded_data)
        decoded_data = base64.urlsafe_b64decode(decoded_data + b'=' * (-len(decoded_data) % 4))
        print(decoded_data)


if __name__ == "__main__":
    URL: str = sys.argv[1]
    if "http" not in URL:
        URL = f"http://{URL}"
    HUB_SRC: str = sys.argv[2]  # в uleb

    print(URL)
    res = requests.post(URL)
    while res.status_code != 204:
        print(res.content)
        res = requests.post(URL)
    # if res.status_code == 200:
    #
    # elif res.status_code == 204:
    #     sys.exit(0)
    # else:
    #     sys.exit(99)
# python main.py localhost:9998 ef0
