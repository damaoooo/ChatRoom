import socket
from utils import *
from typing import List


class User:
    def __init__(self, expire_time: int, private_socket: socket.socket):
        self.expire_time = expire_time
        self.private_socket = private_socket
        self.block_list: List[str] = []
        self.send_list: List[Message] = []

    def add_block(self, username):
        if username in self.block_list:
            raise CustomError("user_already_block", "user already block")
        if username not in AllUserList:
            raise CustomError("user_not_exist", "User Not Exist")
        self.block_list.append(username)

    def remove_block(self, username):
        if username not in self.block_list:
            raise CustomError("user_not_found_in_block_list", "User Not Found In Block List")
        self.block_list.remove(username)


OnlineUserList: List[User] = []
AllUserList: List[str] = []


