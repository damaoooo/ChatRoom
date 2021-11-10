from dataclasses import dataclass


@dataclass()
class Message:
    type: str
    to: str
    content: str


class CustomError(Exception):
    def __init__(self, error_type, error_info):
        super().__init__(self)  # 初始化父类
        self.error_info = error_info
        self.error_type = error_type

    def __str__(self):
        return self.error_type + ':' + self.error_info

