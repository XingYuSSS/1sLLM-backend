from client import ModelProvider
import time

class Test(ModelProvider):
    def __init__(self):
        super().__init__('test', 'http://localhost:8000', debug=True)

    def generate_stream(self, msg_list):
        result = 'test: ' + msg_list[-1]['content']
        for i in result:
            time.sleep(0.1)
            yield i

if __name__ == '__main__':
    test = Test()
    test.run()