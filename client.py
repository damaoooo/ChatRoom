import socket
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
            print(r)
            s = input().encode()
            self.s.send(s)

    def command_parser(self, command: str):

        m = Message("whoelse", "", "")
        if command.startswith("message"):  # TODO: split command as Message
            c = command.split(' ')
            if len(c) < 3:
                print("Not a good message command")
                print("message <user> <message>")
            m = Message(c[0], c[1], ' '.join(c[2:]))

        elif command.startswith("whoelse"):
            m = Message("whoelse", "", "")

        elif command.startswith('logout'):
            m = Message("logout", "", "")
            self.go_die(m)

        self.tcp_unit.send_message(m)

    def run(self):
        self.authentication()
        self.tcp_unit.start()
        threading.Thread(target=self.get_message).start()
        while 1:
            try:
                if kbhit():
                    message = input()
                    self.command_parser(message)
                if self.die:
                    break
            except KeyboardInterrupt:
                self.go_die(Message("go die", "", "User Abort"))
                exit(-1)

    def get_message(self):
        while 1:
            m: Message = self.tcp_unit.get_message()
            if 'reply_' in m.type:
                print(m.content)
            elif 'go die' == m.type:
                print(m.content)
                return

    def go_die(self, reason):
        # TODO: end ALL threads and exit
        self.die = True
        self.tcp_unit.go_die(reason)


c = Client(7676)
c.run()