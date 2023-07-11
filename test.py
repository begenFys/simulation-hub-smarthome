import json
obj = {"name" : "John"}
obj_json = json.dumps(obj)
print(obj_json)
print(obj_json.encode())