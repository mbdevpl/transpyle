
class MyTypicalClass:

    def __init__(self, arg1: int, arg2: int):
        self.arg1 = arg1
        self.arg2 = arg2

    def check(self) -> bool:
        return self.arg1 == self.arg2
