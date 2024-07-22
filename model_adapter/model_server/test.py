from server import ModelProvider

class Test(ModelProvider):
    def __init__(self):
        super().__init__('test', '0.0.0.0:7081')

    def generate_fn(self, msg_list) -> str:
        return 'test: ' + msg_list[-1]['content']

if __name__ == '__main__':
    test = Test()
    test.run()