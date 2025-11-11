from .base_mixer import BaseMixer


class MixerSender(BaseMixer):
    def __init__(
        self, ip: str, port: int,
        connection_timeout: int = 20
    ) -> None:
        super().__init__(ip, port, connection_timeout=connection_timeout)
        self.connect()
        self.alive_thread.join()
        self.receiving_thread.join()

    def receiving_thread(self) -> None:
        ''' Sink Thread '''
        # We need to listen to the Connection to keep
        # the alive ping thread connected
        # But as this is the sender we do not need to keep track
        # of the messages
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

    def fx_mute(self, input, value, datatype, fx_index) -> None:
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
