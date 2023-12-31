# Здесь были написаны задачи, которые я поставил себе по началу выполнения задания, сейчас я в попыхах дописываю
# обработку STATUS у EnvSensor.
# Я сделал гитхаб, где написал неплохой README, можете ознакомиться, открою его после завершения заявок.
# github - https://github.com/begenFys/simulation-hub-smarthome
# для оперативной связи - https://t.me/begenFys
# TODO - что нужно будет сделать
# в общем планированию реализовать класс hub, который будет отсылать запросы и хранить список сенсоров, устройств
# посылать запросы и принимать
# 1. Кодирование декодирование packet из base64 +
# 2. Подключение к серверу +
# 3. Изучить типы завершения программы, как их менять +
# 4. Прописать случаи завершения программы +
# 5. uleb128 посмотреть что это +
# 6. crc кодирование конечной суммы payload +
# 7. работа с разными типами устройств +
# 8. проверка на игнор пакета(гарантируется ли?) +
from datetime import datetime
# TODO - какие функции пригодятся
# 1. Функция из 16 вида в ULEB128 и наоборот +
# 2. Функция crc8 +
# 3. Функция перевода из строки в список байтов и наоборот

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
TIME: int = 0
TIMEOUT: int = 0
TIMEOUT_FLAG: bool = True


class CMD:  # чтобы в циферках не запутаться)
    WHOISHERE = 1
    IAMHERE = 2
    GETSTATUS = 3
    STATUS = 4
    SETSTATUS = 5
    TICK = 6


class DEV:
    HUB = 1
    ENV_SENSOR = 2
    SWITCH = 3
    LAMP = 4
    SOCKET = 5
    CLOCK = 6


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


def get_uleb128_from_bytearray(data: bytearray) -> bytearray:
    data_len = uleb128_length(data)
    return bytearray(data[:data_len])


# преобразуем строк в нужный нам вид
def str_to_bytearray(data: str) -> bytearray:
    byte_array = bytearray()
    byte_array.append(len(data))
    byte_array.extend(data.encode())
    return byte_array


def bytearray_to_str(data: bytearray) -> bytearray:
    ind = 0
    str_len = data[ind]
    ind += 1
    string = data[ind: ind + str_len]
    return string


class UrlCoder:
    @staticmethod
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

    @staticmethod
    def get_cmd_body(cmd_body: bytearray) -> Dict:
        dev_name = bytearray_to_str(cmd_body).decode()
        dev_props = cmd_body[len(dev_name) + 1:]
        return {"dev_name": dev_name, "dev_props": dev_props}

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

        serial_length = uleb128_length(payload[ind:])
        payload_json["serial"] = uleb128_decode(payload[ind:ind + serial_length]) if serial_length > 1 else payload[ind]
        ind += serial_length
        payload_json["dev_type"] = payload[ind]
        ind += 1
        payload_json["cmd"] = payload[ind]
        ind += 1
        if ind < len(payload):
            if payload_json["cmd"] in (CMD.WHOISHERE, CMD.IAMHERE):
                payload_json["cmd_body"] = UrlCoder.get_cmd_body(payload[ind:])
            else:
                payload_json["cmd_body"] = payload[ind:]  # разные случаи
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

        def split_packets(data: bytearray) -> List[Dict]:
            packets = []
            ind = 0
            while ind < len(data):
                packet = {"length": data[ind], "payload": bytearray(), "crc8": 0}
                ind += 1
                packet["payload"] = data[ind:ind + packet["length"]]
                ind += packet["length"]
                packet["crc8"] = data[ind]
                if packet["crc8"] == UrlCoder.calculate_crc8(packet["payload"]):  # игнор пакет, если crc8 не совпадает
                    packets.append(packet)
                ind += 1
            return packets

        # основной код
        data = base64_to_bytearray(response_base64)
        if data:
            packets = split_packets(data)
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
        packet.append(UrlCoder.calculate_crc8(payload))
        return packet

    @staticmethod
    def encode(packets: List[bytearray]) -> bytes:
        data = bytearray()
        for packet in packets:
            data.extend(packet)
        data = base64.urlsafe_b64encode(data)
        while b"=" in data:
            data = data.replace(b"=", b"")
        return data


# Классы устройств
class Device():
    def __init__(self, src: int, dev_type: int, dev_name: str) -> None:
        self.src = src
        self.dev_type = dev_type
        self.dev_name = dev_name


class Hub:  # Затычка для SWITCH
    pass


class EnvSensor(Device):
    def __init__(self, src: int, dev_type: int, dev_name: str, dev_props: bytearray) -> None:
        super().__init__(src, dev_type, dev_name)
        self.dev_props = self.__parse_dev_props(dev_props)
        self.__serial = 2  # serial 2 потому что когда мы создаём экземпляр класса, то это приходит от запроса IAMHERE, где serial уже 1

    def __parse_dev_props(self, data: bytearray):
        ind = 0
        sensors = data[ind]
        sensors_dict = {}
        for i in range(4):
            if sensors & 2 ** i:
                sensors_dict[i] = []

        ind += 1  # BAD
        # вот там был лишний байт из-за которого всё ломалось 0х04
        # такое ощущение что это параметр кол-ва триггеров о котором не сказали....

        ind += 1
        while ind < len(data):
            temp = {"on": None, "name": None, "oper": None,
                    "value": None}  # у датчика наверняка можно поставить больше и меньше
            op = data[ind]
            temp["on"] = op & 1
            op >>= 1
            temp["oper"] = op & 1
            op >>= 1
            ind += 1

            value = get_uleb128_from_bytearray(data[ind:])
            if isinstance(value, int):
                temp["value"] = value
                ind += 1
            else:
                temp["value"] = uleb128_decode(value)
                ind += len(value)

            name = bytearray_to_str(data[ind:])
            temp["name"] = name.decode()
            ind += len(name) + 1

            sensors_dict[op].append(temp)

        return sensors_dict

    @property
    def serial(self) -> int:
        self.__serial += 1
        return self.__serial - 1

    def IAMHERE(self):
        payload = UrlCoder.encode_payload(self.src, BROADCAST_DST, self.__serial, self.dev_type, CMD.IAMHERE)

        cmd_body = bytearray()
        cmd_body.extend(str_to_bytearray(self.dev_name))
        sensors = 0
        count_triggers = 0  # непонятный найденный самим параметр
        triggers = bytearray()
        for key in self.dev_props.keys():
            sensors |= 2 ** key
            count_triggers += len(self.dev_props[key])
            for trigger in self.dev_props[key]:
                triggers.append((key << 2) | (trigger["oper"] << 1) | trigger["on"])  # преобразуем маску обратно
                triggers.extend(uleb128_encode(trigger["value"]))
                triggers.extend(str_to_bytearray(trigger["name"]))
        cmd_body.append(sensors)
        cmd_body.append(count_triggers)
        cmd_body.extend(triggers)

        payload.extend(cmd_body)
        packet = UrlCoder.encode_packet(payload)
        return packet

    def GETSTATUS(self, hub_src: int) -> bytearray:
        payload = UrlCoder.encode_payload(hub_src, self.src, self.__serial, self.dev_type, CMD.GETSTATUS)
        packet = UrlCoder.encode_packet(payload)
        return packet

    def STATUS(self): # не успел... хотя вроде он и не нужен
        pass


class Switch(Device):
    def __init__(self, src: int, dev_type: int, dev_name: str, dev_props: bytearray) -> None:
        super().__init__(src, dev_type, dev_name)
        self.serial = None
        self.on = None
        self.dev_props = self.__parse_dev_props(dev_props)

    def __parse_dev_props(self, data: bytearray) -> List[str]:
        dev_props = []
        ind = 1  # там опять первый байт кол-во
        while ind < len(data):
            str_len = data[ind]
            ind += 1
            dev_props.append(data[ind: ind + str_len].decode())
            ind += str_len
        return dev_props

    def IAMHERE(self) -> bytearray:
        payload = UrlCoder.encode_payload(self.src, BROADCAST_DST, self.serial, self.dev_type, CMD.IAMHERE)

        cmd_body = bytearray()
        cmd_body.extend(str_to_bytearray(self.dev_name))
        dev_props = bytearray()
        for string in self.dev_props:
            dev_props.extend(str_to_bytearray(string))
        payload.extend(cmd_body)

        packet = UrlCoder.encode_packet(payload)
        return packet

    def GETSTATUS(self, hub_src: int, hub_serial: int) -> bytearray:
        payload = UrlCoder.encode_payload(hub_src, self.src, hub_serial, self.dev_type, CMD.GETSTATUS)
        packet = UrlCoder.encode_packet(payload)
        return packet

    def STATUS(self, on: int, hub: Hub, serial: int) -> List[bytearray]:
        self.serial = serial
        packets = []
        if self.on is None:
            self.on = on

        if self.on != on:
            self.on = on
            for device in hub.devices:
                if device.dev_name in self.dev_props:
                    if device.dev_type == DEV.ENV_SENSOR:
                        raise ("Проверка, что switch не управляет сенсорами")
                    device.STATUS(self.on, self.serial)
                    packets.append(device.SETSTATUS(hub.src, hub.serial))
        return packets


class Lamp(Device):
    def __init__(self, src: int, dev_type: int, dev_name: str) -> None:
        super().__init__(src, dev_type, dev_name)
        self.serial = None
        self.on = None

    def IAMHERE(self) -> bytearray:
        payload = UrlCoder.encode_payload(self.src, BROADCAST_DST, self.serial, self.dev_type, CMD.IAMHERE)
        cmd_body = bytearray()
        cmd_body.extend(str_to_bytearray(self.dev_name))
        payload.extend(cmd_body)
        packet = UrlCoder.encode_packet(payload)
        return packet

    def GETSTATUS(self, hub_src: int, hub_serial: int) -> bytearray:
        payload = UrlCoder.encode_payload(hub_src, self.src, hub_serial, self.dev_type, CMD.GETSTATUS)
        packet = UrlCoder.encode_packet(payload)
        return packet

    def STATUS(self, on: int, serial: int) -> None:
        self.serial = serial
        if on:
            self.on = 1
        else:
            self.on = 0

    def SETSTATUS(self, hub_src: int, hub_serial: int) -> bytearray:
        payload = UrlCoder.encode_payload(hub_src, self.src, hub_serial, self.dev_type, CMD.SETSTATUS)
        payload.append(self.on)  # cmd_body
        packet = UrlCoder.encode_packet(payload)
        return packet


class Socket(Device):
    def __init__(self, src: int, dev_type: int, dev_name: str) -> None:
        super().__init__(src, dev_type, dev_name)
        self.serial = None
        self.on = None

    def IAMHERE(self) -> bytearray:
        payload = UrlCoder.encode_payload(self.src, BROADCAST_DST, self.serial, self.dev_type, CMD.IAMHERE)
        cmd_body = bytearray()
        cmd_body.extend(str_to_bytearray(self.dev_name))
        payload.extend(cmd_body)
        packet = UrlCoder.encode_packet(payload)
        return packet

    def GETSTATUS(self, hub_src: int, hub_serial: int) -> bytearray:
        payload = UrlCoder.encode_payload(hub_src, self.src, hub_serial, self.dev_type, CMD.GETSTATUS)
        packet = UrlCoder.encode_packet(payload)
        return packet

    def STATUS(self, on: int, serial: int) -> None:
        self.serial = serial
        if on:
            self.on = 1
        else:
            self.on = 0

    def SETSTATUS(self, hub_src: int, hub_serial: int) -> bytearray:
        payload = UrlCoder.encode_payload(hub_src, self.src, hub_serial, self.dev_type, CMD.SETSTATUS)
        payload.append(self.on)  # cmd_body
        packet = UrlCoder.encode_packet(payload)
        return packet


class Hub(Device):
    def __init__(self, src: int, dev_type: int, dev_name: str) -> None:
        super().__init__(src, dev_type, dev_name)
        self.__serial = 1  # REWORK: понять как нормально наследовать статические атрибуты
        self.devices = []
        # self.__env_sensors: List[EnvSensor] = []
        # self.__switches: List[Switch] = []
        # self.__lamps: List[Lamp] = []
        # self.__sockets: List[Socket] = []

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

    def IAMHERE(self) -> bytearray:
        payload = UrlCoder.encode_payload(self.src, BROADCAST_DST, self.__serial, self.dev_type, CMD.IAMHERE)

        cmd_body = bytearray()
        cmd_body.extend(str_to_bytearray(self.dev_name))
        payload.extend(cmd_body)

        packet = UrlCoder.encode_packet(payload)
        return packet

    def add_device(self, device: Union[EnvSensor, Switch, Lamp, Socket]) -> None:
        self.devices.append(device)

    def contain_device(self, device: Union[EnvSensor, Switch, Lamp, Socket]) -> bool:
        return device in hub.devices

    def trigger_devise(self, dev_name: str, cmd_body: int, serial: int):
        for device in hub.devices:
            if device.dev_name == dev_name:
                device.STATUS(cmd_body[0], serial)
                return device.SETSTATUS(self.src, self.__serial)
                break
    def device_STATUS(self, device: Union[EnvSensor, Switch, Lamp, Socket], cmd_body: bytearray, serial: int) -> List[bytearray]:
        packets = []
        if device.dev_type == DEV.SWITCH:
            on = cmd_body[0]
            packets_switch = device.STATUS(on, self, serial)
            if packets_switch:
                packets.extend(packets_switch)
        elif device.dev_type in (DEV.LAMP, DEV.SOCKET):
            on = cmd_body[0]
            if device.on is None:
                device.STATUS(on, serial)

            if device.on != on:
                device.STATUS(on, serial)
                packets.append(device.SETSTATUS(self.src, self.__serial))
        elif device.dev_type == DEV.ENV_SENSOR:  # в последнюю очередь делалось, возможно не работает
            packets_envsensors = []
            ind = 0
            values = []
            while ind < len(cmd_body):
                value = get_uleb128_from_bytearray(cmd_body[ind:])
                values.append(value)
                ind += len(value)

            ind = 0
            for key in device.dev_props.keys():

                triggers = device.dev_props[key]
                for trigger in triggers:
                    val_edge = trigger["value"]
                    if trigger["oper"] == 1:
                        if values[ind] > val_edge:
                            packets_envsensors.extend(self.trigger_devise(trigger["name"], triggers["on"], serial))
                    else:
                        if values[ind] < val_edge:
                            packets_envsensors.extend(self.trigger_devise(trigger["name"], triggers["on"], serial))
                ind += 1

            if packets_envsensors:
                packets.extend(packets_envsensors)

        return packets

    def devices_IAMHERE(self) -> List[bytearray]:
        packets = []
        for device in self.devices:
            packets.append(device.IAMHERE())
        return packets

    def devices_GETSTATUS(self) -> List[bytearray]:
        packets = []
        for device in self.devices:
            if device.dev_type != DEV.CLOCK:
                packets.append(device.GETSTATUS(self.src, self.__serial))

        return packets


# Класс Client - для отправки запросов
class Client:
    URL = "http://localhost:9998"

    @staticmethod
    def post(data: Union[str, bytes]) -> requests.Response:
        res = requests.post(URL, data=data)
        return res


if __name__ == "__main__":
    URL: str = sys.argv[1]
    if "http" not in URL:
        URL = f"http://{URL}"
    Client.URL = URL
    HUB_SRC: int = int(sys.argv[2], 16)

    hub = Hub(HUB_SRC, DEV.HUB, "HUB01")
    PACKETS.append(hub.WHOISHERE())
    while True:
        if PACKETS:
            data = UrlCoder.encode(PACKETS)
        else:
            data = ""  # просто отправляем пустой запрос, тикаем таймер
        res = Client.post(data)
        PACKETS.clear()
        if res.status_code == 200:
            data = UrlCoder.decode(res.content)
            for packet in data:
                payload = packet["payload"]
                if payload["dev_type"] == DEV.CLOCK and payload["cmd"] == CMD.TICK:
                    TIME = uleb128_decode(payload["cmd_body"])
                    TIMEOUT += 100
                    print(TIME, TIMEOUT)
                    if TIMEOUT > 300:
                        TIMEOUT -= 300
                        TIMEOUT_FLAG = False
                elif payload["cmd"] == CMD.WHOISHERE or (payload["cmd"] == CMD.IAMHERE and TIMEOUT_FLAG):
                    if payload["cmd"] == CMD.WHOISHERE:
                        PACKETS.append(hub.IAMHERE())
                        PACKETS.extend(hub.devices_IAMHERE())

                    if payload["dev_type"] == DEV.ENV_SENSOR:
                        env_sensor = EnvSensor(payload["src"], DEV.ENV_SENSOR, payload["cmd_body"]["dev_name"],
                                               payload["cmd_body"]["dev_props"])
                        if not hub.contain_device(env_sensor):
                            hub.add_device(env_sensor)
                    elif payload["dev_type"] == DEV.SWITCH:
                        switch = Switch(payload["src"], DEV.SWITCH, payload["cmd_body"]["dev_name"],
                                        payload["cmd_body"]["dev_props"])
                        if not hub.contain_device(switch):
                            hub.add_device(switch)
                    elif payload["dev_type"] == DEV.LAMP:
                        lamp = Lamp(payload["src"], DEV.LAMP, payload["cmd_body"]["dev_name"])
                        if not hub.contain_device(lamp):
                            hub.add_device(lamp)
                    elif payload["dev_type"] == DEV.SOCKET:
                        socket = Socket(payload["src"], DEV.SOCKET, payload["cmd_body"]["dev_name"])
                        if not hub.contain_device(socket):
                            hub.add_device(socket)

                elif payload["cmd"] == CMD.STATUS and TIMEOUT_FLAG:
                    for device in hub.devices:
                        if device.src == payload["src"]:
                            PACKETS.extend(hub.device_STATUS(device, payload["cmd_body"], payload["serial"]))
                            break

            if TIMEOUT == 300:  # прошло максимальное время, можно отправлять снова
                PACKETS.extend(hub.devices_GETSTATUS())
            TIMEOUT_FLAG = True
        elif res.status_code == 204:
            sys.exit(0)
        else:
            sys.exit(99)

# python main.py localhost:9998 ef0
