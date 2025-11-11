from .base_mixer import BaseMixer

import paho.mqtt.client as mqtt
from queue import Queue
from os import path


class MqttSender():
    def __init__(
        self, host: str = "localhost", port: int = 1883,
        queue: str = "config"
    ) -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.connect(host, port)
        self.queue = queue

    def send_message(self, topic: str, message: str | int | float) -> None:
        self.client.publish(path.join(self.queue, topic), message)


class MixerListener(BaseMixer):
    def __init__(
        self, ip: str, port: int,
        queue: Queue = None,
        connection_timeout: int = 20,
        mqtt_queue: str = None,
        mqtt_host: str = "localhost",
        mqtt_port: int = 1883
    ) -> None:
        super().__init__(ip, port)
        # Add a queue to share received messages
        self.queue = queue
        self.mqtt_client = None
        if mqtt_queue:
            self.mqtt_client = MqttSender(mqtt_host, mqtt_port, mqtt_queue)
        self._check_delivery()
        self.connect()
        self.alive_thread.join()
        self.recv_thread.join()

    def receiving_thread(self):
        ''' Receiving Thread
            Listen for messages from Soundcraft Ui16.
            Format them and put them in the message queue `queue`
        '''
        buffer = ""
        while not self.exit.is_set():
            # save new data to buffer
            buffer += self.client.recv(2048).decode()
            if "\n" not in buffer:
                # If no message delimiter is found wait for new messages
                continue
            # split buffer on delimiter into parts
            parts = buffer.split("\n")
            # Save everything except last unfinished element
            data = parts[0:len(parts)-1]
            # set unfinished back in buffer
            buffer = parts[len(parts)-1]
            for message in data:
                if "SETD" not in message:
                    continue
                if self.queue:
                    self.queue.put(self._format_setd_message(message))
                if self.mqtt_client:
                    topic, message = self._format_mqtt_message(message)
                    self.mqtt_client.send_message(topic, message)

    def _format_mqtt_message(self, message):
        """ Format a received SETD message into a topic and message for mqtt
            publishing
        """
        _, body, value = message.split("^")
        body_list = body.split(".")
        return ("/".join(body_list), value)

    def _format_setd_message(self, message) -> dict:
        ''' Format a received SETD message into dict from string '''
        _, body, value = message.split('^')
        body_list = body.split('.')
        output = {}
        if body_list[0] == "var":
            output["var"] = body_list[1]
        elif len(body_list) == 3:
            output["channel"] = body_list[1]
            output["function"] = body_list[2]
        elif len(body_list) == 4:
            output["channel"] = body_list[1]
            output["option"] = body_list[2]
            output["function"] = body_list[3]
        elif len(body_list) == 5:
            output["channel"] = body_list[1]
            output["option"] = body_list[2]
            output["option_channel"] = body_list[3]
            output["function"] = body_list[4]
        elif body_list[0] == "m":
            output["channel"] = body_list[1]
        elif body_list[0] == "afs":
            output["option"] = body_list[1]
        else:
            output["error"] = ".".join(body_list)
        output["kind"] = body_list[0]
        output["value"] = value
        return output

    def _check_delivery(self) -> None:
        """ Checks if a valid delivery Method is set """
        if not self.queue and not self.mqtt_client:
            raise RuntimeError(
                "No delivery method was set. "
                "Please make sure to set a Queue and/or mqtt_queue"
            )
