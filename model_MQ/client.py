import json
from typing import Generator
from abc import ABC, abstractmethod
import time

import redis

    
class StreamMQ():
    def __init__(self, redis_client: redis.Redis, stream_name) -> None:
        self.client = redis_client
        self.stream_name = stream_name

    def send(self, message):
        print(message)
        self.client.xadd(
            self.stream_name,
            {k: json.dumps(v) for k, v in message.items()},
        )

    def read(self, count=1, block=None):
        result = self.client.xread({self.stream_name: '0'}, count=count, block=block)
        print(result)
        if result is None or result == []:
            return []
        self.client.xdel(self.stream_name, *[t[0] for t in result[0][1]])
        return [{k: json.loads(v) for k, v in t[1].items()} for t in result[0][1]]
    
    def read_all(self, block=None):
        return self.read(count=None, block=block)
    
class StreamGroupProducer():
    def __init__(self, redis_client: redis.Redis, stream_name, group_name='default') -> None:
        self.client = redis_client
        self.stream_name = stream_name
        self.group_name = group_name
        if not self.client.exists(stream_name) or all(info['name'] !=group_name for info in self.client.xinfo_groups(stream_name)):
            self.client.xgroup_create(stream_name, group_name, mkstream=True) 

    def send(self, message):
        print(message)
        self.client.xadd(
            self.stream_name,
            {k: json.dumps(v) for k, v in message.items()},
        )


class StreamGroupConsumer():
    def __init__(self, redis_client: redis.Redis, stream_name, consumer_name=None, group_name='default') -> None:
        self.client = redis_client
        self.stream_name = stream_name
        self.consumer_name = consumer_name if consumer_name is not None else str(time.time())
        self.group_name = group_name
        if not self.client.exists(stream_name) or all(info['name'] !=group_name for info in self.client.xinfo_groups(stream_name)):
            self.client.xgroup_create(stream_name, group_name, mkstream=True) 
        self.client.xgroup_createconsumer(stream_name, group_name, self.consumer_name)

    def read(self, count=1, block=None):
        result = self.client.xreadgroup(self.group_name, self.consumer_name, {self.stream_name: '>'}, count=count, block=block)
        print(result)
        if result is None or result == []:
            return []
        self.client.xack(self.stream_name, self.group_name, *[t[0] for t in result[0][1]])
        return [{k: json.loads(v) for k, v in t[1].items()} for t in result[0][1]]
    
    def read_all(self, block=None):
        return self.read(count=None, block=block)
    


class ModelProvider(ABC):
    def __init__(self, model_id, redis_host, redis_port, redis_db, redis_password, node_id=None):
        self.model_id = model_id
        self.node_id = node_id
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
        )
        self.registerMQ = StreamMQ(self.redis_client, 'register')
        self.cmdMQ = StreamGroupConsumer(self.redis_client, f'{model_id}_cmd', node_id)

    def _register(self):
        self.registerMQ.send({'register': self.model_id})

    def run(self):
        while True:
            self._register()
            message = self.cmdMQ.read(block=30_000)
            if message == []:
                continue
            message = message[0]
            if message['cmd'] == 'generate':
                self._generate(message)
            elif message['cmd'] == 'generate_stream':
                self._generate_stream(message)


    def _generate(self, data):
        gen_id = data['gen_id']
        result = self.generate_fn(data['msg_list'])
        response = {'model': self.model_id, 'code': 1, 'message': result}
        StreamMQ(self.redis_client, f'{gen_id}_generate').send({'response': response})

    def _generate_stream(self, data):
        gen_id = data['gen_id']
        sendMQ = StreamMQ(self.redis_client, f'{gen_id}_generate')
        iterator = self.generate_stream(data['msg_list'])
        for i in iterator:
            trunk = {'model': self.model_id, 'code': 1, 'message': i}
            sendMQ.send({'response': trunk, 'status': 'generating'})
        sendMQ.send({'status': 'finish'})

    def generate_fn(self, msg_list) -> str:
        """
        Generate response based on the message list.
        :param msg_list: [{'role': 'system'/'assistant'/'user', 'content': str}]
        :return: str
        """
        result = ''
        for i in self.generate_stream(msg_list):
            result += i
        return result

    @abstractmethod
    def generate_stream(self, msg_list) -> Generator[str, None, None]:
        """
        Generate response based on the message list.
        :param msg_list: [{'role': 'system'/'assistant'/'user', 'content': str}]
        :return:  A generator that yields the next token generated by model.
        """
        raise NotImplementedError