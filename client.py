import time
import argparse
from utils import *


class Timer:
    def __init__(self, duration: int):
        self.start_time = int(time.time())
        self.duration = duration

    def update(self):
        self.start_time = int(time.time())

    def check(self):
        now = int(time.time())
        return now - self.start_time < self.duration


class Client:
    def __init__(self, server_port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('127.0.0.1', server_port))
        self.queue_size = 32
        self.die = False
        self.timer = Timer(60)
        self.username = ""
        self.p2p_username = ""
        self.p2p_unit = None
        self.p2p_sock = None
        self.p2p_wait = True
        self.p2p_client_sock = None
        self.p2p_state = 'close'
        self.tcp_unit = TCPUnit(self.s, queue.Queue(self.queue_size))

    def init_p2p_s(self):
        ps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ps.bind(('localhost', 0))
        ps.listen()
        port = ps.getsockname()[1]
        self.p2p_sock = ps
        threading.Thread(target=self._p2p_accept).start()
        return str(port)

    def _p2p_accept(self):
        self.p2p_sock.settimeout(2)
        while self.p2p_wait:
            try:
                conn, _ = self.p2p_sock.accept()
                self.p2p_client_sock = conn
                self.p2p_wait = False
                self.set_p2p_unit()
                return
            except socket.timeout:
                continue

    def set_p2p_unit(self):
        if self.p2p_client_sock == None:
            print('Not get p2p_client_sock')
        self.p2p_unit = TCPUnit(self.p2p_client_sock, queue.Queue(self.queue_size))
        self.p2p_unit.start()

    def connect(self, port):
        self.p2p_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p2p_client_sock.connect(('localhost', port))
        self.p2p_state = 'open'
        self.set_p2p_unit()

    def destroy_p2p(self, reason):
        self.p2p_wait = False
        if self.p2p_sock:
            self.p2p_sock: socket.socket
            self.p2p_sock.close()
            if self.p2p_unit:
                self.p2p_unit: TCPUnit
                self.p2p_unit.go_die(Message("go die", "", reason))
                self.p2p_unit = None
            self.p2p_sock = None

        if self.p2p_client_sock:
            self.p2p_client_sock.close()
            if self.p2p_unit:
                self.p2p_unit: TCPUnit
                self.p2p_unit.go_die(Message("go die", "", reason))
                self.p2p_unit = None
            self.p2p_client_sock = None
        self.p2p_state = 'close'

    def authentication(self):
        print("Login ... ")
        while 1:
            r = self.s.recv(4096).decode()
            if r.startswith('Success'):
                print("Success Login!")
                self.username = r.split('|')[1]
                return True
            elif "you are blocked" in r:
                print(r)
                return False
            print(r)
            s = input().encode()
            self.s.send(s)

    def command_parser(self, command: str):
        m = Message("whoelse", "", "")
        if command.startswith("message"):
            c = command.split(' ')
            if len(c) < 3:
                print("Not a good message command")
                print("message <user> <message>")
                return
            m = Message(c[0], c[1], ' '.join(c[2:]))

        elif command == 'whoelse':

            m = Message("whoelse", "", "")

        elif command.startswith("whoelsesince"):
            c = command.split(' ')
            if len(c) != 2 or c[0] != "whoelsesince":
                print("Not a good whoelsesince command")
                print("whoelsesince <time>")
                return
            m = Message(c[0], c[1], "")

        elif command.startswith('logout'):
            m = Message("logout", "", "User Log Out")
            self.tcp_unit.send_message(m)
            self.go_die(m)
            return

        elif command.startswith("broadcast"):
            c = command.split(' ')
            if len(c) < 2 or c[0] != 'broadcast':
                print("Not a good broadcast command")
                print("broadcast <message>")
                return
            m = Message(c[0], "", ' '.join(c[1:]))

        elif command.startswith("message"):
            c = command.split(' ')
            if len(c) < 3 or c[0] != "message":
                print("Not a good message command")
                print("message <user> <message>")
                return
            m = Message(c[0], c[1], ' '.join(c[2:]))

        elif command.startswith("block"):
            c = command.split(' ')
            if len(c) != 2 or c[0] != "block":
                print("Not a good block command")
                print("block <user>")
                return
            m = Message(c[0], c[1], "")

        elif command.startswith("unblock"):
            c = command.split(' ')
            if len(c) != 2 or c[0] != "unblock":
                print("Not a good unblock command")
                print("unblock <user>")
                return
            m = Message(c[0], c[1], "")

        elif command.startswith('startprivate'):
            c = command.split(' ')
            if len(c) != 2 or c[0] != 'startprivate':
                print("Not a good startprivate command")
                print("startprivate <user>")
                return
            p = self.init_p2p_s()
            self.timer.update()
            m = Message(c[0], c[1], p)
            print(f"Waiting {c[1]} to receive p2p request.")

        elif command.startswith('private'):
            c = command.split(' ')
            if len(c) < 3 or c[0] != "private":
                print("Not a good private command")
                print("private <user> <message>")
                return
            if self.p2p_state != 'open':
                print("Error. Establish p2p with one user first.")
                return
            elif self.p2p_username != c[1]:
                print("Error. Not connection with this user.")
                return
            else:
                m = Message(c[0], c[1], ' '.join(c[2:]))
                self.p2p_unit: TCPUnit
                self.p2p_unit.send_message(m)
                self.timer.update()
                return

        elif command.startswith('stopprivate'):
            c = command.split(' ')
            if len(c) != 2 or c[0] != 'stopprivate':
                print("Not a good stopprivate command")
                print("stopprivat <user>")
                return
            if c[1] != self.p2p_username:
                print(f"Error. No Connection with User {c[1]}")
                return
            else:
                m = Message(c[0], c[1], "")
                self.timer.update()
                self.p2p_unit.send_message(m)
                self.destroy_p2p('user cancel')
                print(f"disconnected with {c[1]}")
                return

        else:
            print("Unsupported command")
            print("Usage:")
            print("message <user> <message>")
            print("broadcast <message>")
            print("whoelse")
            print("whoelsesince <time>")
            print("block <user>")
            print("unblock <user>")
            print("logout")
            print("startprivate <user> ")
            print("private <user> <message>")
            print("stopprivate <user>")
            return

        self.tcp_unit.send_message(m)

    def run(self):
        if not self.authentication():
            exit(0)
        self.tcp_unit.start()
        threading.Thread(target=self.get_message).start()
        while 1:
            try:
                if self.die:
                    return
                if kbhit():
                    message = input('command>>')
                    if len(message) < 1:
                        continue
                    self.command_parser(message)

            except KeyboardInterrupt:
                self.go_die(Message("go die", "", "User Abort"))
                exit(-1)

    def get_message(self):
        while 1:
            time.sleep(0.01)
            if not self.tcp_unit.recv_queue.empty():
                m: Message = self.tcp_unit.get_message()

                if 'reply_' in m.type:
                    print(m.content)

                elif 'go die' == m.type:
                    self.die = True
                    self.tcp_unit.die = True
                    print(m.content)
                    return

                elif m.type == "broadcast" or m.type == 'message':
                    self.message_print(m)

                elif 'logout' == m.type:
                    print(m.content)
                    self.go_die(Message("go die", "", ""))
                    return

                elif m.type == 'startprivate':
                    reply = Message("private_reply", "", "")
                    reply.to = m.to
                    res = input(f"User {m.to} want to start p2p with you, connect?(Y/N) default (N)")
                    if res == 'Y':
                        reply.content = 'Y'
                        self.tcp_unit.send_message(reply)
                        self.connect(int(m.content))
                        self.p2p_username = m.to
                        self.p2p_state = 'open'
                        print(f"p2p with {m.to} as client connected.")
                        self.timer.update()
                    else:
                        reply.content = 'N'
                        self.tcp_unit.send_message(reply)

                elif m.type == 'private_reply':
                    if m.content == 'N':
                        print(f"User {m.to} Refused your p2p attempt.")
                        self.destroy_p2p("user refused")
                    elif m.to == 'server':
                        print(m.content)
                        self.destroy_p2p(m.content)
                    elif m.content == 'Y':
                        print(f"p2p with {m.to} as server connected.")
                        self.p2p_state = 'open'
                        self.p2p_username = m.to
                        self.timer.update()

            if self.p2p_state == 'open':
                if self.p2p_unit:
                    self.p2p_unit: TCPUnit
                    if not self.p2p_unit.recv_queue.empty():
                        m = self.p2p_unit.get_message()
                        if m.type == 'private':
                            self.message_print(m)
                        elif m.type == 'stopprivate':
                            self.destroy_p2p('user canceled')
                            print(f"User {self.p2p_username} disconnected")
                    if not self.timer.check():
                        self.p2p_unit.send_message(Message("stopprivate", self.p2p_username, ""))
                        self.destroy_p2p('time out!')
                        print(f"time out! disconnected with {self.p2p_username}")

    def go_die(self, reason):
        self.die = True
        self.tcp_unit.go_die(reason)
        exit(-1)

    def message_print(self, m: Message):
        t = time.time()
        t = time.localtime(t)
        t = time.strftime("%H:%M:%S", t)
        print(f"{m.type} - {m.to} - {t}:")
        print(m.content)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('args', type=int)
    a = a.parse_args()
    c = Client(a.args)
    c.run()
