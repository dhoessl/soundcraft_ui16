from .base_mixer import BaseMixer
from threading import Thread


class MixerSender(BaseMixer):
    def __init__(
            self, ip: str, port: int,
            connection_timeout: int = 20,
            logger_name: str = "MixerSender"
    ) -> None:
        super().__init__(
            ip, port,
            connection_timeout=connection_timeout,
            logger_name=logger_name
        )
        self.recv_thread = Thread(
            target=self.sink_thread,
            args=()
        )

    def start(self) -> None:
        self.connect()
        if self.connected:
            self.alive_thread.start()
            self.recv_thread.start()
        else:
            self.logger.critical(
                "Sender could not connect to Mixer. Exiting Sender!"
            )

    def sink_thread(self) -> None:
        """ Thread to listen and discard messages
            This is required to keep the keepalive thread working
        """
        while not self.exit.is_set():
            _ = self.client.recv(2048).decode()

    def master(self, value) -> None:
        cmd = f'SETD^m.mix^{value}\n'
        self.send_packet(cmd)

    def mix(self, channel, value, kind) -> None:
        self.send_packet(f'SETD^{kind}.{channel}.mix^{value}\n')

    def mute(self, channel, value, kind) -> None:
        self.send_packet(f'SETD^{kind}.{channel}.mute^{value}\n')

    def fx(self, channel, value, kind, index) -> None:
        self.send_packet(f'SETD^{kind}.{channel}.fx.{index}.value^{value}\n')

    def fx_mute(self, input, value, datatype, fx_index -> None):
        self.send_packet(
            f'SETD^{datatype}.{input}.fx.{fx_index}.mute^{value}\n'
        )

    def tempo(self, value) -> None:
        for channel in range(1, 4):
            self.send_packet(f'SETD^f.{channel}.bpm^{value}\n')

    def record(self) -> None:
        self.send_packet("RECTOGGLE\n")

    def easy_eq(self, kind, channel, index, value) -> None:
        self.send_packet(f'SETD^{kind}.{channel}.eq.b{index}.gain^{value}\n')

    def fx_setting(self, fx, par, value) -> None:
        self.send_packet(f'SETD^f.{fx}.par{par}^{value}\n')

    def send_setd_command(self, body, value) -> None:
        cmd = f'SETD^{body}^{value}\n'
        self.client.send(cmd.encode("UTF-8"))

    def send_packet(self, command) -> None:
        self.client.send(command.encode("UTF-8"))
