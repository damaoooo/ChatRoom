import socket


class Client:
    def __init__(self, server_port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('127.0.0.1', server_port))

    def run(self):
        print("start")
        while 1:

            s = input().encode()
            self.s.send(s)
            print(self.s.recv(4096).decode())


c = Client(7676)
c.run()