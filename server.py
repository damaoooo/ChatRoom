from utils import *
import time
from typing import List, Dict
import threading


class User:
    def __init__(self, username: str, password: str, expire_time: int):
        self.expire_time = expire_time
        self.username = username
        self.password = password
        self.login_time = int(time.time())
        self.update_time = int(time.time())
        self.block_list: List[str] = []
        self.queue_size = 32
        self.die = False
        self.tcp_unit = None

    def activate(self, conn: socket.socket):
        self.tcp_unit = TCPUnit(conn, recv_queue=queue.Queue(self.queue_size))
        self.login_time = int(time.time())
        self.update_time = int(time.time())
        self.die = False
        m = Message("broadcast", "system", f"User {self.username} online!")
        self._broadcast(m, system=True)

        if MessageBuffer.__contains__(self.username):
            while MessageBuffer[self.username]:
                self.send(MessageBuffer[self.username].pop())

    def update(self):
        self.update_time = int(time.time())

    def timer(self):
        while 1:
            time.sleep(0.05)
            if self.die:
                return
            t = int(time.time())
            if t - self.update_time > self.expire_time:
                self.go_die(Message("go die", "", "Time Expire"), send=True)
                break

    def go_die(self, reason, send=False):
        m = Message("broadcast", "system", f"User {self.username} offline!")
        self._broadcast(m, system=True)
        if send:
            self.tcp_unit.send_message(reason)
        self.tcp_unit.go_die(reason)
        self.die = True
        self.tcp_unit.recv_queue.put(reason)
        self.tcp_unit.sock.close()
        OnlineUserList.pop(self.username)

    def send(self, m):
        self.tcp_unit.send_message(m)

    def main_loop(self):
        threading.Thread(target=self.timer).start()  # TODO: online and offline broadcast
        while 1:
            if self.die:
                break
            m: Message = self.tcp_unit.get_message()
            if m.type == 'go die':
                return
            self.update()

            if m.type == 'whoelse':
                res = self._whoelse()
                m = Message('', '', '')
                m.to = self.username
                m.type = "reply_whoelse"
                m.content = res
                self.send(m)

            elif m.type == 'logout':
                self.go_die(m)

            elif m.type == 'broadcast':
                self._broadcast(m)

            elif m.type == 'message':
                self._message(m)

            elif m.type == 'block':
                self._block(m)

            elif m.type == 'unblock':
                self._unblock(m)

    def _whoelse(self):
        res = []
        for k in OnlineUserList:
            if k == self.username or k in self.block_list:
                continue
            res.append(k)
        return '\n'.join(res)

    def _broadcast(self, m: Message, system=False):
        new_m = m
        new_m.to = self.username
        for u in AllUserList.keys():
            if self.username in AllUserList[u].block_list or u == self.username:
                continue
            if u in OnlineUserList:
                OnlineUserList[u].send(new_m)
            else:
                if not system:
                    if u in MessageBuffer:
                        MessageBuffer[u].append(new_m)
                    else:
                        MessageBuffer[u] = [new_m]
        if not system:
            reply_m = Message("reply_broadcast", "server", "message could not be sent to some recipients.")
            self.send(reply_m)

    def _message(self, m: Message):
        reply_m = Message("", "", "")

        if m.to not in AllUserList.keys():
            reply_m.type = "reply_message"
            reply_m.to = self.username
            reply_m.content = "Error. Invalid user"

        elif m.to in OnlineUserList.keys():
            if self.username in OnlineUserList[m.to].block_list:
                new_m = Message("reply_message", "server", f"You have been blocked by {m.to}.")
                self.send(new_m)
            else:
                new_m = Message(type=m.type, to=m.to, content=m.content)
                new_m.to = self.username
                oppo = OnlineUserList[m.to]
                oppo.send(new_m)
        else:
            if self.username in AllUserList[m.to].block_list:
                new_m = Message("reply_message", "server", f"You have been blocked by {m.to}.")
                self.send(new_m)
            else:
                new_m = Message(type=m.type, to=m.to, content=m.content)
                new_m.to = self.username
                if m.to in MessageBuffer:
                    MessageBuffer[m.to].append(new_m)
                else:
                    MessageBuffer[m.to] = [new_m]

    def _block(self, m: Message):
        reply = Message("reply_block", "", "")
        if m.to in self.block_list:
            reply.content = "Error. User Already Blocked in Block List."
        elif m.to not in AllUserList.keys():
            reply.content = "Error. User Not Exist."
        else:
            self.block_list.append(m.to)
            reply.content = f"Block User {m.to} Success!"
        self.send(reply)

    def _unblock(self, m: Message):
        reply = Message("reply_unblock", "", "")
        if m.to in self.block_list:
            self.block_list.remove(m.to)
            reply.content = f"Unblock User {m.to} Success!"
        else:
            reply.content = f"Error. User {m.to} Not in Block List!"
        self.send(reply)

    def __str__(self):
        t = time.localtime(self.login_time)
        t = time.strftime("%Y-%m-%d %H:%M:%S", t)
        return f"User: {self.username} - login {t}"

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


MessageBuffer: Dict[str, List[Message]] = {}  # TODO: When user open his window, display history message
OnlineUserList: Dict[str, User] = {}
AllUserList: Dict[str, User] = {}


class Timer:
    def __init__(self, duration: int):
        self.duration = duration
        self.block_list: Dict[str, int] = {}

    def update(self):
        current_time = int(time.time())
        pop_list = []
        for k in self.block_list.keys():
            delta = current_time - self.block_list[k]
            if delta >= self.duration:
                pop_list.append(k)
        for i in pop_list:
            self.block_list.pop(i)

    def put(self, user: str):
        self.block_list[user] = int(time.time())

    def remain(self, username: str):
        return self.duration - (int(time.time()) - self.block_list[username])

    def __contains__(self, item):
        return item in self.block_list.keys()


class Server:
    def __init__(self, server_port: int, block_duration: int, timeout: int):
        self.server_port = server_port
        self.block_duration = block_duration
        self.timeout = timeout
        self.queue_size = 32
        self.buf_size = 4096
        self.read_file()
        self.timer = Timer(block_duration)
        self.sock: socket.socket = self.prepare_socket()

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
            AllUserList[username] = User(username, password, self.timeout)

    def authentication(self, conn_socket: socket.socket):
        self.timer.update()
        conn_socket.send("Welcome, Input Your Username:".encode())
        username = conn_socket.recv(self.buf_size).decode().replace('\n', '')
        debug_print(f'user input username {username}')

        if username in OnlineUserList.keys():
            conn_socket.send("User Already Login".encode())
            conn_socket.close()
            return False, ''

        elif username in self.timer:
            conn_socket.send("Your account is blocked due to multiple login failures. Please try again later".encode())
            conn_socket.close()
            return False, ''

        elif username not in AllUserList.keys():
            conn_socket.send("New User, Input Your Password".encode())
            password = conn_socket.recv(self.buf_size).decode().replace('\n', '')
            debug_print(f'user input password {password}')
            AllUserList[username] = User(username, password, self.timeout)
            conn_socket.send("Success".encode())
            return True, username
        else:
            conn_socket.send("Input password:".encode())
            for i in range(3):
                password = conn_socket.recv(self.buf_size).decode().replace('\n', '')
                debug_print(f'user input password {password}')
                if password != AllUserList[username].password:
                    if i < 2:
                        conn_socket.send("Invalid password, Input Again:".encode())
                        continue
                    else:
                        conn_socket.send("Invalid password 3 times, you are blocked".encode())
                        return False, ""
                else:
                    conn_socket.send("Success".encode())
                    return True, username
            return False, ''

    def main_loop(self):
        while True:
            conn, addr = self.sock.accept()
            debug_print(f'{addr} - connected!')
            threading.Thread(target=self.pre_run, args=(conn, addr)).start()

    def pre_run(self, conn, addr):
        state, username = self.authentication(conn)
        if state:
            self.run(AllUserList[username], conn)

    def run(self, user: User, conn: socket.socket):
        OnlineUserList[user.username] = user
        user.activate(conn)
        user.tcp_unit.start()
        user.main_loop()


s = Server(7676, 20, 600)
s.main_loop()
