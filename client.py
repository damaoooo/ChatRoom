import socket
import time

from utils import *
import platform


class Client:
    def __init__(self, server_port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('127.0.0.1', server_port))
        self.queue_size = 32
        self.die = False
        self.tcp_unit = TCPUnit(self.s, queue.Queue(self.queue_size))

    def authentication(self):
        print("Login ... ")
        while 1:
            r = self.s.recv(4096).decode()
            if r == 'Success':
                print("Success Login!")
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

        elif command.startswith("whoelse"):
            m = Message("whoelse", "", "")

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
            m = Message(c[0], c[1], "")

        else:
            print("Unsupported command")
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


c = Client(7676)
c.run()
