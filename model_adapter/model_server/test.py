from server import ModelProvider
import time

class Test(ModelProvider):
    def __init__(self):
        super().__init__('test', '0.0.0.0:7081')

    def generate_stream(self, msg_list):
        result = 'test: ' + msg_list[-1]['content']
        for i in result:
            time.sleep(0.1)
            yield i

if __name__ == '__main__':
    test = Test()
    test.run()