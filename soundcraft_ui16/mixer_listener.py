from .base_mixer import BaseMixer
from queue import Queue
from threading import Thread


class MixerListener(BaseMixer):
    def __init__(self, ip: str, port: int, queue: Queue, connection_timeout: int = 20) -> None:
        super().__init__(ip, port)
        # Add a queue to share received messages
        self.queue = queue
        self.recv_thread = Thread(
            target=self.receive_thread,
            args=()
        )

    def start(self):
        """ Try to connect to mixer.
            Starts the keep_alive and receiver Threads
        """
        self.connect()
        if self.connected:
            self.alive_thread.start()
            self.recv_thread.start()
        else:
            print("ERROR: Listener could not connect to Mixer.")
            exit(1)

    def receive_thread(self):
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
            # split buffer on delimiter into pars
            parts = buffer.split("\n")
            # Save everything execpt last unfinished element
            data = parts[0:len(parts)-1]
            # set unfinished back in buffer
            buffer = parts[len(parts)-1]
            for message in data:
                if "SETD" in message:
                    self.queue.put(self._format_setd_message(message))

    def _format_setd_message(self, message):
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
