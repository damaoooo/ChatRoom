from utils import *
import time
from typing import List, Dict
import threading


class User:
    def __init__(self, expire_time: int, private_socket: socket.socket):
        self.expire_time = expire_time
        self.private_socket = private_socket
        self.block_list: List[str] = []
        self.send_list: List[Message] = []

    def add_block(self, username):
        if username in self.block_list:
            return False, 'User Already In Block List'
        elif username not in AllUserList.keys():
            return False, "User Not Exist"
        else:
            self.block_list.append(username)
            return True, ''

    def remove_block(self, username):
        if username not in self.block_list:
            return False, 'User Not In Block List'
        else:
            self.block_list.remove(username)
            return True, ''


OnlineUserList: List[User] = []
AllUserList: Dict[str, str] = {}


class Timer:
    def __init__(self, duration: int):
        self.duration = duration
        self.block_list: Dict[socket.socket, int] = {}

    def update(self):
        current_time = int(time.time())
        pop_list = []
        for k in self.block_list.keys():
            delta = current_time - self.block_list[k]
            if delta >= self.duration:
                pop_list.append(k)
        for i in pop_list:
            self.block_list.pop(i)

    def put(self, conn: socket.socket):
        self.block_list[conn] = int(time.time())

    def remain(self, conn: socket.socket):
        return self.duration - (int(time.time()) - self.block_list[conn])

    def __contains__(self, item):
        return item in self.block_list.keys()


class Server:
    def __init__(self, server_port: int, block_duration: int, timeout: int, debug=True):
        self.server_port = server_port
        self.block_duration = block_duration
        self.debug = debug
        self.timeout = timeout
        self.buf_size = 4096
        self.read_file()
        self.timer = Timer(block_duration)
        self.sock: socket.socket = self.prepare_socket()

    def debug_print(self, content):
        if self.debug:
            print(content)

    def prepare_socket(self) -> socket.socket:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', self.server_port))
        s.listen()
        return s

    def read_file(self, path='./credentials.txt'):
        with open(path, 'r') as f:
            lines = f.readlines()
            f.close()
        for line in lines:
            username, password = line.replace('\n', '').split(' ')
            AllUserList[username] = password

    def authentication(self, conn_socket: socket.socket):
        username = conn_socket.recv(self.buf_size).decode().replace('\n', '')
        self.debug_print(f'user input username{username}')
        if username in OnlineUserList:
            conn_socket.send("User Already Login".encode())
            conn_socket.close()
            return False
        elif username not in AllUserList:
            conn_socket.send("New User".encode())
            password = conn_socket.recv(self.buf_size).decode().replace('\n', '')
            self.debug_print(f'user input password {password}')
            AllUserList[username] = password

            return True
        else:
            for i in range(3):
                conn_socket.send("Input password".encode())
                password = conn_socket.recv(self.buf_size).decode().replace('\n', '')
                self.debug_print(f'user input password {password}')
                if password != AllUserList[username]:
                    conn_socket.send("Invalid password".encode())
                    continue
                else:
                    return True
            return False

    def main_loop(self):
        while True:
            conn, addr = self.sock.accept()
            self.debug_print(f'{addr} - connected!')
            threading.Thread(target=self.run, args=(conn, addr)).start()

    def run(self, conn, addr):
        while not self.authentication(conn):
            self.timer.put(conn)
            while 1:
                self.timer.update()
                if conn not in self.timer:
                    break
                rw, ww, ew = select.select([conn], [conn], [conn])
                for r in rw:
                    _ = conn.recv(self.buf_size)
                    conn.send(f'You are blocked until {self.timer.remain(conn)} seconds\n'.encode())
        print("Next")



s = Server(7676, 7, 7)
s.main_loop()



