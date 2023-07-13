import urllib.parse
import base64
import json

def base64_url_decode(inp):
    return base64.urlsafe_b64decode(inp + b'=' * (4 - len(inp) % 4))

#print(base64_url_decode(b"DbMG_38SBgbMi6f3lDF4"))

h = b'\r\xb3\x06\xff\x7f\x14\x06\x06\x94\x8d\xa7\xf7\x941\x14'

packets = [
    {
        "length": 13,
        "payload": {
            "src": 819,
            "dst": 16383,
            "serial": 1,
            "dev_type": 6,
            "cmd": 6,
            "cmd_body": {
                "timestamp": 1688984021000
            }
        },
        "crc8": 138
    }
]

# json -> str
json_str = "".join(json.dumps(packets).split()) # игнор пробельных знаков

# str -> bytes
encode_str = "".join(json.dumps(packets).split()).encode("utf-8")

# bytes -> base64url
base64url = base64.urlsafe_b64encode(encode_str)

print(json_str)
print(base64url)
print(base64.urlsafe_b64decode(base64url))
print(base64.urlsafe_b64decode(base64url).decode())
print(json.loads(base64.urlsafe_b64decode(base64url).decode()))