import json
import queue
import select
import socket
import threading
from dataclasses import dataclass

debug = True


def debug_print(content):
    if debug:
        print(content)


try:
    from msvcrt import kbhit
except ImportError:
    import termios, fcntl, sys, os


    def kbhit():
        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)
        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
        try:
            while True:
                try:
                    c = sys.stdin.read(1)
                    return True
                except IOError:
                    return False
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)


@dataclass()
class Message:
    type: str
    to: str
    content: str

    def __str__(self):
        return json.dumps({"type": self.type, "to": self.to, "content": self.content})


class CustomError(Exception):
    def __init__(self, error_type, error_info):
        super().__init__(self)  # 初始化父类
        self.error_info = error_info
        self.error_type = error_type

    def __str__(self):
        return self.error_type + ':' + self.error_info


class TCPUnit:
    def __init__(self, s: socket.socket, recv_queue: queue.Queue):
        self.sock = s
        self.split = b'\xf0\x0f'
        self.buf_size = 4096
        self.queue_len = 32
        self.die = False
        self.recv_queue = recv_queue

    def start(self):
        threading.Thread(target=self.recv_message).start()

    def send_message(self, m: Message):
        b = str(m).encode()
        b += self.split
        self.sock.send(b)

    def go_die(self, reason):
        self.recv_queue.put(reason)
        self.die = True

    def new_package(self, t: bytes):
        r = json.loads(t)
        new_m = Message('', '', '')
        new_m.to = r['to']
        new_m.content = r['content']
        new_m.type = r['type']
        return new_m

    def get_message(self):
        return self.recv_queue.get()

    def recv_message(self):
        buffer = b''
        while 1:
            try:
                if self.die:
                    return
                rw, ww, xw = select.select([self.sock], [self.sock], [self.sock], 0.01)
                if rw:
                    r = self.sock.recv(self.buf_size)
                    if len(r) == 0:
                        continue
                    buffer += r
                    buffer = buffer.split(self.split)
                    for i in range(len(buffer) - 1):
                        p = buffer.pop(0)
                        if p == b'' or (b'{' not in p and '}' not in p):
                            continue
                        debug_print(p)
                        p = self.new_package(p)
                        self.recv_queue.put(p)
                    buffer = self.split.join(buffer)
            except (ConnectionResetError, OSError, ValueError):
                self.go_die(Message("go die", "", "Connection Reset Error"))
