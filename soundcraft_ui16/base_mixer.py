from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Event
from time import sleep
from logging import getLogger, INFO


class BaseMixer:
    def __init__(
            self, ip: str,
            port: int,
            connection_timeout: int = 20,
            logger_name: str = "BaseMixer"
    ) -> None:
        self.ip = ip
        self.port = port
        self.connection_timeout = connection_timeout
        self.logger = getLogger(logger_name)
        if self.logger.level < 20:
            self.logger.setLevel(INFO)

        self.client = None
        self.exit = Event()
        self.alive_thread = Thread(
            target=self.keep_alive_thread,
            args=()
        )
        self.recv_thread = None
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
                        self.logger.warning(
                            f"Unable to reach {self.ip}"
                        )
                    connect_count += 1
                elif oserr.errno == 101:
                    self.logger.critical(
                        f"Network of {self.ip} is not reachable"
                    )
                    exit(1)
                elif oserr.errno == 103:
                    self.logger.error(
                        f"Connection to {self.ip} aborted. Retry"
                    )
                else:
                    self.logger.error(
                        f"Unexpected OSError => {oserr.errno}\n\t"
                        "Error appeared while connecting to Mixer"
                    )
                sleep(1)
            except Exception as ex:
                self.logger.error(f"Unexpected error: {ex}")

    def keep_alive_thread(self) -> None:
        ''' Thread '''
        while not self.exit.is_set():
            self.send_alive(5)
        self.logger.warning("Keepalive exited")

    def send_alive(self, wait: int = 0) -> None:
        try:
            self.client.send(b"ALIVE\n")
        except socket.timeout:
            self.logger.error("Timeout while send alive")
            self.connected = False
            return
        except ConnectionResetError:
            self.logger.critical("Connection reset by remote")
            self.exit.set()
            return
        sleep(wait)

    def terminate(self) -> None:
        # Need to set exit_event since otherwise threads wont stop
        self.exit.set()
        if self.alive_thread.is_alive():
            self.alive_thread.join()
        if self.recv_thread.is_alive():
            self.recv_thread.join()
        try:
            self.client.close()
            if self.connected:
                self.logger.info('Disconnected from SoundCraft gracefully.')
            self.connected = False
        except Exception as ex:
            self.logger.error("Abnormal termination")
            self.logger.error(f"Execption: {ex}")
