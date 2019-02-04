
class MyTypicalClass:

    def __init__(self, arg1: int, arg2: int):
        self.arg1 = arg1
        self.arg2 = arg2

    def check(self) -> bool:
        return self.arg1 == self.arg2

    def do_sth(self, my_arg: int) -> None:
        if my_arg < 0:
            print('negative')
        elif my_arg > 0:
            print('positive')
        else:
            print('zero')
        if my_arg % 2 == 0:
            print('even')
        else:
            print('odd')
        if my_arg == 42:
            print('the answer')
