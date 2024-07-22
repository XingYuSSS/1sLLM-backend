import json
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from .base import Api

class Qwen_Api(Api):
    def __init__(self, api_key) -> None:
        super().__init__(api_key=api_key)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def _list_models(self):
        url = "https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope/"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table', class_='table')

            models = []
            for row in table.tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols: 
                    cells = cols[1].find_all('p')
                    for cell in cells:
                        model_name = cell.text.strip()
                        models.append(model_name)

            return models[1:]
        else:
            print("Failed to retrieve the webpage")
            return []

    def _get_response(self, chat, model_id):
        try:
            msg_list = [msg.to_role_dict() for msg in chat.get_msg_list()]
            completion = self.client.chat.completions.create(
                model=model_id,
                messages=msg_list,
            )
            data = {'model': model_id, 'code': 1, 'message': completion.choices[0].message.content}
        except Exception as e:
            print(e)
            data = {'model': model_id, 'code': 0, 'message': str(e)}
        return data
