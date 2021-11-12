import socket


class Client:
    def __init__(self, server_port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('127.0.0.1', server_port))

    def authentication(self):
        print("Login ... ")
        while 1:
            r = self.s.recv(4096).decode()
            if r == 'Success':
                return True
            print(r)
            s = input().encode()
            self.s.send(s)


c = Client(7676)
c.authentication()