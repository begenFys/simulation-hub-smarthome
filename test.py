from main import UrlCoder, EnvSensor, uleb128_encode, uleb128_decode

query = b"OAL_fwQCAghTRU5TT1IwMQ8EDGQGT1RIRVIxD7AJBk9USEVSMgCsjQYGT1RIRVIzCAAGT1RIRVI09w"
packet = UrlCoder.decode(query)
payload = packet[0]["payload"]
env = EnvSensor(payload["src"], payload["dev_type"], payload["cmd_body"]["dev_name"], payload["cmd_body"]["dev_props"])
print(env.dev_props)
p = [env.IAMHERE()]
print(p)
payload = UrlCoder.decode(UrlCoder.encode(p))[0]["payload"]
env1 = EnvSensor(payload["src"], payload["dev_type"], payload["cmd_body"]["dev_name"], payload["cmd_body"]["dev_props"])


print(env.GETSTATUS(int("ef0", 16)))
