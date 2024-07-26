import http.client
import json
from openai import OpenAI
from .base import Api
import ssl
import certifi

class OpenAI_agent_Api(Api):
    def __init__(self, api_key) -> None:
        super().__init__(api_key=api_key)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.chatanywhere.tech/v1",
        )
    
    def _list_models(self):
        if self.api_key is None:
            return []
        
        conn = http.client.HTTPSConnection(
            "api.chatanywhere.tech",
            context=ssl.create_default_context(cafile=certifi.where())
        )
        payload = ''
        headers = {
            'Authorization': 'Bearer ' + self.api_key,
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
        }
        conn.request("GET", "/v1/models", payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        data = json.loads(data)['data']
        data = [item['id'] for item in data]
        return data
    
    def _get_response(self, chat, model_id):
        try:
            msg_list = [msg.to_role_dict() for msg in chat.get_msg_list()]
            completion = self.client.chat.completions.create(
                model=model_id,
                messages=msg_list
            )
            data = {'model': model_id, 'code': 1, 'message': completion.choices[0].message.content}
        except Exception as e:
            print(e)
            data = {'model': model_id, 'code': 0, 'message': str(e)}
        return data

    def _get_response_stream(self, chat, model_id):
        try:
            msg_list = [msg.to_role_dict() for msg in chat.get_msg_list()]
            chunks = self.client.chat.completions.create(
                model=model_id,
                messages=msg_list,
                stream=True
            )
            iterator = [{'model': model_id, 'code': 1, 'message': chunk.choices[0].delta.content} for chunk in chunks]
        except Exception as e:
            print(e)
            iterator = [{'model': model_id, 'code': 0, 'message': str(e)}]
        return iterator