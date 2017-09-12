import argparse
import random
import socket
from multiprocessing import Process

import datetime

parser = argparse.ArgumentParser(description="Reverse shell multi-handler")
parser.add_argument('--control-port', type=int, default=5555, help="TCP port to use for the "
                                                                   "multi-handler client "
                                                                   "connections")
parser.add_argument('--shell-port', type=int, default=4444, help="TCP port to use for reverse shells")

args = parser.parse_args()

sessions = []
server_started = datetime.datetime.now()
PROMPT = '=> '


def total_sessions() -> int:
    s = 0
    for host in sessions:
        s += len(sessions[host])
    return s


class Connection(Process):
    def __init__(self, conn: socket.socket, addr: str):
        self.conn = conn
        self.addr = addr
        super().__init__()

    def conni(self):
        welcome = "Server started at {}. {} session{} active.\n".format(
            server_started,
            len(sessions),
            "s" if not len(sessions) == 1 else "")
        self.conn.send(welcome.encode())
        welcome = "Type (l) to list sessions, and (i) to interact with a session.\n"
        self.conn.send(welcome.encode())
        while True:
            self.conn.send(PROMPT.encode())
            r = self.conn.recv(1024).decode().strip()
            if r == 'l':
                session_list = "Active sessions:\n"
                for n, session in enumerate(sessions):
                    session_list += "({}) {}\n".format(n, session[0])
                self.conn.send(session_list.encode())
            elif r.startswith('i'):



class StoppableServer(Process):
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(10)
        self._stop = False
        super().__init__()

    def stop(self) -> None:
        self._stop = True

    def stopped(self) -> bool:
        return self._stop


class ShellServer(StoppableServer):
    def __init__(self, host: str="0.0.0.0", port: int=4444):
        super().__init__(host, port)

    def run(self) -> None:
        print("Listening for shell connections")
        while not self.stopped():
            conn, addr = self.shell_sock.accept()
            sessions.append((addr, conn))
        self.sock.close()


class ControlServer(StoppableServer):
    def __init__(self, host: str ='127.0.0.1', port: int=5555):
        self.connections = []
        super().__init__(host, port)

    def serve(self) -> None:
        print("Listening for control connections...")
        while not self.stopped():
            c = Connection(*self.sock.accept())
            self.connections.append(c)
            c.conni()
        self.sock.close()


if __name__ == '__main__':
    ss = ShellServer(port=args.shell_port)
    rand = random.randint(1024, 65535)
    print(rand)
    cs = ControlServer(port=rand)  # args.control_port)
    try:
        cs.serve()
        ss.start()
    except (KeyboardInterrupt, Exception) as e:
        cs.stop()
        ss.stop()
        raise e
