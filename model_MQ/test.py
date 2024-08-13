from client import ModelProvider
import time

class Test(ModelProvider):
    def __init__(self):
        super().__init__(
            'test', 
            redis_host='',
            redis_port='',
            redis_db='',
            redis_password='',
            node_id=''
        )

    def generate_stream(self, msg_list):
        result = 'test: ' + msg_list[-1]['content']
        for i in result:
            time.sleep(0.1)
            yield i

if __name__ == '__main__':
    test = Test()
    test.run()