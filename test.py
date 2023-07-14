class Dog:
    def __init__(self, name):
        self.name = name

class Animals:
    def __init__(self):
        self.animals = []

    def add(self, anim):
        self.animals.append(anim)

def rev(string):
    return string[::-1]

ani = Animals()
d1 = Dog("Nick")