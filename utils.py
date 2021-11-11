import json
import socket
from dataclasses import dataclass
import select


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


class TCPUnit:
    def __init__(self, s: socket.socket):
        self.sock = s
        self.split = b'\xf0\x0f'
        self.buf_size= 4096

    def send_message(self, m: Message):
        b = str(m).encode()
        b += self.split
        self.sock.send(b)

    def recv_message_wait(self):
        r = self.sock.recv(self.buf_size)
        r = r.split(self.split)[0]
        r = json.loads(r)
        new_m = Message('', '', '')
        new_m.__dict__ = r
        return
