import socketio
import time
import eventlet

class ModelProvider:
    def __init__(self, model_id, server_url='0.0.0.0:7081', debug=False):
        self.sio = socketio.Server(cors_allowed_origins='*', logger=debug, engineio_logger=debug)
        self.model_id = model_id
        self.server_port = int(server_url.split(':')[-1])
        self._setup_events()
        self.app = socketio.WSGIApp(self.sio)
        self.adapter_sid_list = []

    def _setup_events(self):
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('registered', self._on_registered)
        self.sio.on('generate', self._on_generate)

    def _on_connect(self, sid, environ):
        self.adapter_sid_list.append(sid)
        print('Connection established')
        self.sio.emit('register', {'model_id': self.model_id}, to=sid)

    def _on_disconnect(self, sid):
        print('Disconnected from server')

    def _on_registered(self, sid, data):
        print(f"Registered response: {data}")

    def _on_generate(self, sid, data):
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
        eventlet.wsgi.server(eventlet.listen(('', self.server_port)), self.app)
