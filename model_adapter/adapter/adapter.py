import socketio

class Adapter:
    def __init__(
        self,
        server_url='http://localhost:8000',
        model_url='http://localhost:7081',
        debug=False,
    ):
        self.server_sio = socketio.Client(logger=debug, engineio_logger=debug)
        self.model_sio = socketio.Client(logger=debug, engineio_logger=debug)
        self.server_url = server_url
        self.model_url = model_url
        self._setup_events()
        self.server_sio.connect(self.server_url)
        self.model_sio.connect(self.model_url)


    def _setup_events(self):
        self.server_sio.on('connect', self._on_connect)
        self.server_sio.on('disconnect', self._on_disconnect)
        self.server_sio.on('registered', self._on_registered)
        self.server_sio.on('generate', self._on_generate)
        self.server_sio.on('generate_stream', self._on_generate_stream)

        self.model_sio.on('connect', self._on_connect)
        self.model_sio.on('disconnect', self._on_disconnect)
        self.model_sio.on('register', self._on_register)
        self.model_sio.on('generate_finish', self._on_generate_finish)
        self.model_sio.on('generate_streaming', self._on_generate_streaming)
        self.model_sio.on('generate_stream_finish', self._on_generate_stream_finish)

    def _on_connect(self):
        print('Connection established')

    def _on_disconnect(self):
        print('Disconnected from server')
        exit(0)

    def _on_register(self, data):
        print(f"Register: {data}")
        self.server_sio.emit('register', data=data)

    def _on_registered(self, data):
        print(f"Registered: {data}")
        self.model_sio.emit('registered', data=data)

    def _on_generate(self, data):
        print(f"generate: {data}")
        self.model_sio.emit('generate', data=data)

    def _on_generate_finish(self, data):
        print(f"generate finish: {data}")
        self.server_sio.emit('generate_finish', data=data)

    def _on_generate_stream(self, data):
        print(f"generate stream: {data}")
        self.model_sio.emit('generate_stream', data=data)

    def _on_generate_streaming(self, data):
        self.server_sio.emit('generate_streaming', data=data)

    def _on_generate_stream_finish(self, data):
        print(f"generate stream finish: {data}")
        self.server_sio.emit('generate_stream_finish', data=data)

    def run(self):
        while True:
            self.server_sio.wait()
            self.model_sio.wait()

    def disconnect(self):
        self.server_sio.disconnect()
        self.model_sio.disconnect()

if __name__ == '__main__':
    adapter = Adapter(server_url='http://localhost:8000')
    adapter.run()