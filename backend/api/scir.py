from .base import Api
import time
from typing import Dict

from middle_ware.redis import StreamMQ, StreamGroupProducer

class ModelMQ:
    def __init__(self):
        self.registerMQ = StreamMQ('register')
        self.models: Dict[str, StreamMQ] = {}

    def get_models(self):
        for message in self.registerMQ.read_all():
            print(message)
            if (key := message['register']) not in self.models:
                self.models[key] = StreamGroupProducer(f'{key}_cmd')
        return list(self.models.keys())

    def generate(self, cid, msg_list, model_id):
        gen_id = f'{cid}{time.time()}'
        self.models[model_id].send({'gen_id': gen_id, 'msg_list': msg_list, 'cmd': 'generate'})
        result = StreamMQ(f'{gen_id}_generate').read(block=1000_000_000)[0]['response']
        print(result)
        return result

    def generate_stream(self, cid, msg_list, model_id):
        gen_id = f'{cid}{time.time()}'
        self.models[model_id].send({'gen_id': gen_id, 'msg_list': msg_list, 'cmd': 'generate_stream'})

        resultMQ = StreamMQ(f'{gen_id}_generate')
        while (result := resultMQ.read(block=1000_000_000)[0])['status'] != 'finish':
            print(result)
            yield result['response']

class Scir_Api(Api):
    server = ModelMQ()
    server.get_models()

    def __init__(self, api) -> None:
        super().__init__()

    def _list_models(self):
        model = self.server.get_models()
        return model

    def _get_response(self, chat, model_id):
        self.server.get_models()
        msg_list = [msg.to_role_dict() for msg in chat.get_msg_list()]
        return self.server.generate(chat.get_chat_id(), msg_list, model_id)

    def _get_response_stream(self, chat, model_id):
        self.server.get_models()
        msg_list = [msg.to_role_dict() for msg in chat.get_msg_list()]
        return self.server.generate_stream(chat.get_chat_id(), msg_list, model_id)