from .base import Api
import socketio
import time

class SocketServer:
    def __init__(self):
        self.sio = socketio.Server(cors_allowed_origins='*')
        
        self.sio.on('connect', self.sio_connect)
        self.sio.on('disconnect', self.sio_disconnect)
        self.sio.on('register', self.sio_register)
        self.sio.on('generate_finish', self.sio_generate_finish)
        self.models = {}
        self.response_tmp = {}

    def get_wgsiapp(self, wgsiapp):
        return socketio.WSGIApp(self.sio, wgsiapp)

    def generate(self, cid, msg_list, model_id):
        sid = self.models[model_id]
        gen_id = f'{sid}{cid}{time.time()}'
        self.sio.emit('generate', data={'gen_id': gen_id, 'msg_list': msg_list}, to=self.models[model_id])
        while True:
            if gen_id not in self.response_tmp.keys():
                continue
            result = self.response_tmp[gen_id]
            print(result)
            del self.response_tmp[gen_id]
            break
        return result

    @staticmethod
    def sio_connect(sid, environ):
        print(f'{sid} connect')

    def sio_disconnect(self, sid):
        print(f'{sid} disconnect')
        for k, v in self.models.items():
            if v == sid:
                name = k
                break
        del self.models[name]

    def sio_register(self, sid, data):
        print(f'{sid} register {data}')
        self.models[data['model_id']] = sid
        
    def sio_generate_finish(self, sid, data):
        print(f'{sid} generate {data}')
        self.response_tmp[data['gen_id']] = data['response']
    
class Scir_Api(Api):
    server = SocketServer()

    def __init__(self, api) -> None:
        super().__init__()

    def _list_models(self):
        print(list(self.server.models.keys()))
        return list(self.server.models.keys())

    def _get_response(self, chat, model_id):
        msg_list = [msg.to_role_dict() for msg in chat.get_msg_list()]
        return self.server.generate(chat.get_chat_id(), msg_list, model_id)