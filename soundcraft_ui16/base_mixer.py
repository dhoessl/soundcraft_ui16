from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Event
from time import sleep


class BaseMixer:
    def __init__(self, ip: str, port: int, connection_timeout: int = 20) -> None:
        self.ip = ip,
        self.port = port
        self.connection_timeout = connection_timeout

        self.client = None
        self.exit = Event()
        self.alive_thread = Thread(
            target=self.keep_alive_thread,
            args=()
        )
        self.recv_thrad = None
        self.connected = False

    def connect(self) -> None:
        if self.exit.is_set:
            self.exit.clear()
        self.client = socket(AF_INET, SOCK_STREAM)
        self.client.settimeout(5.0)
        connect_count = 0
        while not self.connected:
            try:
                self.client.connect((self.ip, self.port))
                self.client.send(b"GET /raw HTTP1.1\n\n")
                self.send_alive(0)
                self.connected = True
            except OSError as oserr:
                if oserr.errno == 113:
                    # Wait till remote is reachable
                    if connect_count > self.connect_timeout:
                        print(f"Unable to reach {self.ip} address")
                    connect_count += 1
                    sleep(1)
                else:
                    print(f"Unexpected OSError: {oserr.errno}")
                    print("Error appeared while connecting to Mixer")
            except Exception as ex:
                print(f"Unexpected error: {ex.errno}")

    def keep_alive_thread(self) -> None:
        ''' Thread '''
        while not self.exit.is_set():
            self.send_alive(5)
        print("Keepalive exit")

    def send_alive(self, wait: int = 0) -> None:
        try:
            self.client.send(b"ALIVE\n")
        except socket.timeout:
            print("send_alive timeout")
            self.connected = False
            return
        except ConnectionResetError:
            print("Connection reset by remote")
            self.exit.set()
            return
        sleep(wait)

    def terminate(self):
        # Need to set exit_event since otherwise threads wont stop
        self.exit.set()
        if self.alive_thread.is_alive():
            self.alive_thread.join()
        if self.recv_thread.is_alive():
            self.recv_thread.join()
        try:
            self.client.close()
            if self.connected:
                print('Disconnected from SoundCraft gracefully.')
            self.connected = False
        except Exception as ex:  # noqa: E722
            print("Abnormal termination")
            print(f"Execption: {ex}")
