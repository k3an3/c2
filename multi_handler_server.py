import argparse
import datetime
import socket

from multiprocessing import Process

parser = argparse.ArgumentParser(description="Reverse shell multi-handler")
parser.add_argument('--control-port', type=int, default=5555, help="TCP port to use for the "
                                                                   "multi-handler client "
                                                                   "connections")
parser.add_argument('--shell-port', type=int, default=4444, help="TCP port to use for reverse shells")

args = parser.parse_args()

sessions = {}
server_started = datetime.datetime.now()


def total_sessions() -> int:
    s = 0
    for host in sessions:
        s += len(sessions[host])
    return s


class Connection(Process):
    def __init__(self, conn: socket.socket, addr: str):
        self.conn = conn
        self.addr = addr

    def run(self):
        welcome = "Server started at {}. {} session{} active.".format(
            server_started,
            len(sessions),
            "s" if len(sessions) else "")
        self.conn.send(welcome)
        welcome = "Type (l) to list sessions, and (i #) to interact with a session."
        self.conn.send(welcome)
        r = self.conn.recv(100).decode()
        if r == 'l':
            session_list = "Active sessions:\n"
            for n, session in enumerate(sessions):
                session_list += "({}) {}\n".format(n, session.addr)
            self.conn.send(session_list)


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

    def run(self):
        print("Listening for shell connections")
        while not self.stopped():
            conn, addr = self.shell_sock.accept()
            try:
                sessions[addr].append(conn)
            except TypeError:
                sessions[addr] = [conn]
        self.sock.close()


class ControlServer(StoppableServer):
    def __init__(self, host: str ='127.0.0.1', port: int=5555):
        super().__init__(host, port)

    def serve(self) -> None:
        print("Listening for control connections...")
        while not self.stopped():
            Connection(*self.sock.accept()).start()
        self.sock.close()


if __name__ == '__main__':
    #ss = ShellServer(port=args.shell_port)
    cs = ControlServer(port=args.control_port)
    try:
        cs.serve()
    #    ss.start()
    except KeyboardInterrupt:
        cs.stop()
    #    ss.stop()
