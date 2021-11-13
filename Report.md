# Report

## Program Design

### Overview

In order to simplify the program, and in accordance with the requirements of the program, I divided the program into `client.py`, `server.py` and `utils.py`, where `utils.py` contains code that has nothing to do with the server and the client. Such as message definitions, and TCP socket-related functions, and so on. Because TCP-related functions use blocking calls, in order to avoid this problem, I encapsulated TCP-related functions and used `threading` multi-threading for processing. I use a lot of multithreading in the program, such as timers, tcp related functions, message queues, etc., all of which use multithreading a lot.

### TCP backend Design

Because the reception is blocked, and the use of `select` for IO multiplexing requires the setting of timeout. If the timeout is set too high, it will aggravate unnecessary CPU burden, so I used `queue.Queue` in python. As a message queue, since sending does not need to be blocked, and receiving is blocked, you only need to set up a message queue for `recv()`, and then start a multi-thread to receive `recv()`, if you receive To the data, add it to the message queue.

Considering the characteristics of TCP streaming transmission, there will be TCP sticky packets, and the data packets will be truncated. Therefore, I set up a buffer at the receiving message, and each sent data packet ends with a specific byte. When the receiver receives the data stream, it groups the byte stream according to this specific byte, and separates different messages.

Whether it is the client or the server, a thread will be started to fetch `recv_queue`, and when the data of `recv_queue` is obtained, it will act according to the received message

### Client Design

On the client side, it should be noted that if you keep entering `input()` in python, the program will block until the user finishes input, which is not what we want to see. Therefore, I used the `hbhit()` function. When the user's input is detected, the `input()` function is run. On windows, you only need to call `msvcrt.kbhit()`. In a system like `linux`, More troublesome, you need to monitor `sys.stdin`, and only enter `input()` when the user has keyboard input. Since this client is imperative, it is necessary to implement a command parser in the client to parse the user's commands. If the user enters an incorrect command, a prompt should be given. Since p2p communication needs to be communicated with the server at the same time, when the user performs p2p communication, a socket will be reset for private communication

### Server Design

The server stores the information of each user. For users, I designed the user structure to be

```python
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
```

And set a timer, when a certain user exceeds the expire time, then the user will be forced to go offline. Similarly, in P2P communication, there is a similar mechanism.

## Data Structure Design

The user's information is stored in the server, so I designed three `Dict`, of which `OnlineUserList` is used to store current online users, `AllUserList` is used to store all users, the type is `str: User`, where ` str` is the user name, and `User` is the class of the user, and we need to implement the historical message function, that is, when the user is offline, the message will be stored, so I also designed an offline message ` MessageBuffer`, `str: Message`, where str is the user name and `Message` is the message class

In order to express one and transmit the message, I defined the message as a message class, namely Message, which contains three fields, `content: str`, `to: str`, and `type: str`, where type is used to indicate the message type, to is the sender and receiver of the message, content is the content, the following is an example

| type | to | content | meaning |
| --------- | ------ | ------------ | ------------------ |
| whoelse | | | command whoelse |
| message | yoda | hello | send hello to yoda |
| broadcast | system | yoda offline | system broadcast |

## Conclusion

Based on the above design, I used socket, threading and other system native libraries in python, completed the content required in the job, and was able to complete all the functions required by the program documentation