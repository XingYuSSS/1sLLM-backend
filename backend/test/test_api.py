import api

if __name__ == "__main__":
    Qwen = api.Qwen_Api(api_key='')
    print(Qwen.supported_models)

    chat = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "写一篇500字作文，主题是“我的家乡”。"
        }
    ]
    # 计时
    import time
    start = time.time()
    responses = api.Api.get_responses(chat, provider_models={'Qwen': ['qwen-turbo', 'qwen-plus']}, provider_keys= {'Qwen': ''})
    end = time.time()

    print(responses)
    print(end - start)

# from openai import OpenAI
# import os

# def get_response():
#     client = OpenAI(
#         api_key='', # 如果您没有配置环境变量，请在此处用您的API Key进行替换
#         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope SDK的base_url
#     )
#     completion = client.chat.completions.create(
#         model="qwen-plus",
#         messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
#                   {'role': 'user', 'content': '你是谁？'}]
#         )
#     print(completion.model_dump_json())

# if __name__ == '__main__':
#     get_response()