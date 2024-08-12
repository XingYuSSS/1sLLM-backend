import os
import json

import redis
from dotenv import load_dotenv


class Redis():
    def __init__(self) -> None:
        load_dotenv()
        self.client = redis.Redis(
            host=os.environ['REDIS_HOST'],
            port=os.environ['REDIS_PORT'],
            db=os.environ['REDIS_DB'],
            password=os.environ['REDIS_PASSWORD'],
            decode_responses=True,
        )


redis_client = Redis()

class StreamMQ():
    def __init__(self, stream_name) -> None:
        self.client = redis_client.client
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
    def __init__(self, stream_name, group_name='default') -> None:
        self.client = redis_client.client
        self.stream_name = stream_name
        self.group_name = group_name
        if all(info['name'] !=group_name for info in self.client.xinfo_groups(stream_name)):
            self.client.xgroup_create(stream_name, group_name, mkstream=True)        

    def send(self, message):
        print(message)
        self.client.xadd(
            self.stream_name,
            {k: json.dumps(v) for k, v in message.items()},
        )


class StreamGroupConsumer():
    def __init__(self, stream_name, consumer_name, group_name='default') -> None:
        self.client = redis_client.client
        self.stream_name = stream_name
        self.consumer_name = consumer_name
        self.group_name = group_name
        if all(info['name'] !=group_name for info in self.client.xinfo_groups(stream_name)):
            self.client.xgroup_create(stream_name, group_name, mkstream=True) 
        self.client.xgroup_createconsumer(stream_name, group_name, consumer_name)


    def read(self, count=1, block=None):
        result = self.client.xreadgroup(self.group_name, self.consumer_name, {self.stream_name: '>'}, count=count, block=block)
        print(result)
        if result is None or result == []:
            return []
        self.client.xack(self.stream_name, self.group_name, *[t[0] for t in result[0][1]])
        return [{k: json.loads(v) for k, v in t[1].items()} for t in result[0][1]]
    
    def read_all(self, block=None):
        return self.read(count=None, block=block)

