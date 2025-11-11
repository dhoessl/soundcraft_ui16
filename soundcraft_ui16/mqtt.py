import paho.mqtt.client as mqtt


class MqttClient:
    def __init__(
        self, run_forever: bool = True,
        host: str = "localhost", port: int = 1883
    ) -> None:
        self.runforever = run_forever
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def start(self) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(self.host, self.port)
        if self.runforever:
            self.client.loop_forever()
        else:
            self.client.loop_start()

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        self.client.loop_stop()
        raise RuntimeError("Please set an `on_connect` function for client")

    def _on_message(self, client, userdata, msg) -> None:
        print("No _on_message was set - Default Output")
        print(f"{msg.topic} => {msg.payload.decode()}")
