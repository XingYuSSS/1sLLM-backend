import socketio
import time

class ModelProvider:
    def __init__(self, model_id, server_url='http://localhost:8000', debug=False):
        self.sio = socketio.Client(logger=debug, engineio_logger=debug)
        self.server_url = server_url
        self.model_id = model_id
        self._setup_events()
        self.sio.connect(self.server_url)

    def _setup_events(self):
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('registered', self._on_registered)
        self.sio.on('generate', self._on_generate)

    def _on_connect(self):
        print('Connection established')

    def _on_disconnect(self):
        print('Disconnected from server')

    def _on_registered(self, data):
        print(f"Registered response: {data}")

    def _on_generate(self, data):
        result = self.generate_fn(data['msg_list'])
        response = {'model': self.model_id, 'code': 1, 'message': result}
        self.sio.emit('generate_finish', data={'gen_id': data['gen_id'], 'response': response})

    def generate_fn(self, msg_list) -> str:
        """
        Generate response based on the message list.
        :param msg_list: [{'role': 'system'/'assistant'/'user', 'content': str}]
        :return: str
        """
        raise NotImplementedError

    def run(self):
        self.sio.emit('register', {'model_id': self.model_id})
        while True:
            self.sio.wait()

    def disconnect(self):
        self.sio.disconnect()