import base64
import hashlib
import json
import random
import re
import data
from api.base import Api
from flask import Flask, request, session, redirect, Response
from flask_cors import CORS
import socketio
import time
from dotenv import load_dotenv
import os
import requests

import json
# from tencentcloud.common import credential
# from tencentcloud.common.profile.client_profile import ClientProfile
# from tencentcloud.common.profile.http_profile import HttpProfile
# from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# from tencentcloud.sms.v20210111 import sms_client, models

class WebSever:
    def __init__(self):
        self.app = Flask(__name__, static_folder='static', static_url_path='')
        CORS(self.app, supports_credentials=True)
        self.server = data.Server()
        self.socket_server = Api.get_socket_server()
        self.invite_code_manager = data.InviteCodeManager()
        self.app.secret_key = '123456'

        load_dotenv()
        self.TencentConfig = {
            "SecretId": os.getenv('TENCENT_SECRET_ID'),
            "SecretKey": os.getenv('TENCENT_SECRET_KEY'),
            "TemplateId": os.getenv('TENCENT_TEMPLATE_ID'),
            "SignName": os.getenv('TENCENT_SIGN_NAME'),
            "SmsSdkAppId": os.getenv('TENCENT_SMS_SDK_APP_ID')
        }
        self.GuoYangCloud_Config = {
            "appcode": os.getenv("GUOYANG_APPCODE"),
            "smsSignId": os.getenv("GUOYANG_SIGNID"),
            "templateId": os.getenv("GUOYANG_TEMPLATEID")
        }
        self.tmp_sms_code = {}

        # 未登录可用
        self.app.add_url_rule('/', view_func=self.index)
        self.app.add_url_rule('/api/providers', view_func=self.api_providers)
        self.app.add_url_rule('/user/exist', view_func=self.user_exist)
        self.app.add_url_rule('/user/register', view_func=self.user_register)
        self.app.add_url_rule('/user/login', view_func=self.user_login)
        self.app.add_url_rule('/sms/code', view_func=self.sms_code_get)
        # 登录后可用
        self.app.add_url_rule('/user/logout', view_func=self.user_logout)
        self.app.add_url_rule('/api/models', view_func=self.api_models)
        self.app.add_url_rule('/api/list', view_func=self.api_list)
        self.app.add_url_rule('/api/add', view_func=self.api_add)
        self.app.add_url_rule('/api/del', view_func=self.api_del)
        self.app.add_url_rule('/chat/list', view_func=self.chat_list)
        self.app.add_url_rule('/chat/new', view_func=self.chat_new)
        self.app.add_url_rule('/chat/get', view_func=self.chat_get)
        self.app.add_url_rule('/chat/title', view_func=self.chat_title)
        self.app.add_url_rule('/chat/del', view_func=self.chat_del)
        self.app.add_url_rule('/chat/gen', view_func=self.chat_gen)
        self.app.add_url_rule('/chat/gen/stream', view_func=self.chat_gen_stream)
        # self.app.add_url_rule('/chat/regen', view_func=self.chat_regen)
        self.app.add_url_rule('/chat/sel', view_func=self.chat_sel)

        if self.socket_server is not None:
            self.app.wsgi_app = self.socket_server.get_wgsiapp(self.app.wsgi_app)

    def run(self, host='0.0.0.0', port=8000, debug=False):
        self.app.run(host=host, port=port, debug=debug)

    def index(self):
        """
        主页.
        """
        return redirect('index.html')

    def user_exist(self):
        """
        检查用户是否存在.
        """
        username = base64.b64decode(request.args.get('user')).decode('utf-8')
        if self.server.check_user_name_exist(username):
            return json.dumps('user_name_exist'), 200
        return json.dumps('user_name_not_exist'), 200

    def user_register(self):
        """
        注册.
        """
        username = base64.b64decode(request.args.get('user')).decode('utf-8')
        if self.server.check_user_name_exist(username):
            return json.dumps('user_name_exist'), 200
        # 邀请码检查
        invite_code = base64.b64decode(request.args.get('ic')).decode('utf-8')
        if self.invite_code_manager.validate_code(invite_code) == 0:
            return json.dumps('invalid_invite_code'), 200
        elif self.invite_code_manager.validate_code(invite_code) == -1:
            return json.dumps('used_invite_code'), 200
        # 短信验证码检查
        sms_code = base64.b64decode(request.args.get('sc')).decode('utf-8')
        phone = base64.b64decode(request.args.get('phone')).decode('utf-8')
        if sms_code != self.tmp_sms_code[phone]:
            return json.dumps('invalid_sms_code'), 200
        del self.tmp_sms_code[phone]
        
        password = base64.b64decode(request.args.get('pd')).decode('utf-8')
        password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        user = data.User(username, password_md5, phone)
        self.server.add_user(user)

        # 最后标记邀请码
        self.invite_code_manager.mark_code_as_used(invite_code)
        return json.dumps('success'), 200

    def user_login(self):
        """
        登录.
        """
        print("someone trying to login")
        username = base64.b64decode(request.args.get('user')).decode('utf-8')
        password = base64.b64decode(request.args.get('pd')).decode('utf-8')
        if username is None or password is None:
            return json.dumps('invalid_username_or_password'), 401
        password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        # 检查用户名密码
        print(f'Login: {username}, {password}')
        if not self.server.check_user_name_exist(username):
            return json.dumps('invalid_username_or_password'), 401
        if self.server.get_password_md5(username) != password_md5:
            return json.dumps('invalid_username_or_password'), 401
        # 服务器上记录会话信息
        sid = self.server.gen_session_id(username)
        self.server.set_session_dict(username, sid)
        # 客户端cookie中记录会话信息
        session['username'] = username
        session['session_id'] = sid
        return json.dumps('success'), 200

    def user_logout(self):
        """
        登出.
        """
        username = session.get('username')
        if username is None:
            return json.dumps('invalid_username'), 403
        session.pop('username')
        session.pop('session_id')
        self.server.pop_session_dict(username)
        return json.dumps('success'), 200

    def sms_code_get(self):
        """
        获取短信验证码.
        """
        # raise Exception("byd")
        phone = base64.b64decode(request.args.get('phone')).decode('utf-8')
        if not re.match(r'^1[3456789]\d{9}$', phone):
            return json.dumps('invalid_phone'), 200
        sms_code = str(random.randint(100000, 999999))
        # print("#########################")
        # print("sms code:", sms_code)
        # print("phone: ", phone )
        url = "https://gyytz.market.alicloudapi.com/sms/smsSend"

        appcode = self.GuoYangCloud_Config["appcode"]
        smsSignId = self.GuoYangCloud_Config["smsSignId"]
        templateId = self.GuoYangCloud_Config["templateId"]

        param = f'**code**:{sms_code},**minute**:5'
        
        while True:
            try:
                headers = {"Content-Type":"application/x-www-form-urlencoded","Authorization":"APPCODE "+appcode}
                data = {"mobile":phone,"smsSignId":smsSignId,"templateId":templateId,"param":param}
                response = requests.post(url, headers = headers, params = data)
                if response.status_code == 200:
                    print("发送成功")
                    break
                else:
                    raise Exception(f"调用验证码失败,状态码{response.status_code}")


            except Exception as err:
                print(err)
                time.sleep(1)

        self.tmp_sms_code[phone] = sms_code
        return json.dumps('success'), 200

    def api_providers(self):
        """
        获取全局支持的服务商.
        """
        return json.dumps(Api.get_providers()), 200

    def api_models(self):
        """
        获取用户可用的{服务商: 模型列表}.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        user.refresh_model('Scir')
        models = user.get_available_models()
        return json.dumps(models), 200

    def api_list(self):
        """
        获取api列表.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        return json.dumps(user.get_api_dict()), 200

    def api_add(self):
        """
        添加api.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        service_provider_name = base64.b64decode(
            request.args.get('name')).decode('utf-8')
        api_key = base64.b64decode(request.args.get('key')).decode('utf-8')
        if not user.add_api(service_provider_name, api_key):
            return json.dumps('invalid_service_provider_name_or_key'), 200
        return json.dumps('success'), 200

    def api_del(self):
        """
        删除api.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        service_provider_name = base64.b64decode(
            request.args.get('name')).decode('utf-8')
        if service_provider_name not in user.get_api_dict():
            return json.dumps('invalid_service_provider_name'), 403
        user.del_api(service_provider_name)
        return json.dumps('success'), 200

    def chat_title(self):
        """
        修改会话标题.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        chat = self.server.get_chat(user, base64.b64decode(
            request.args.get('cid')).decode('utf-8'))
        if chat is None:
            return json.dumps('invalid_chat_id'), 403
        title = base64.b64decode(request.args.get('title')).decode('utf-8')
        print(title)
        chat.set_title(title)
        return json.dumps('success'), 200

    def chat_list(self):
        """
        获取会话列表.
        """
        print(session.get('username'), session.get('session_id'))
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        return json.dumps(user.get_chat_dict(), default=lambda o: o._to_db_dict(o)), 200

    def chat_new(self):
        """
        新建会话.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        # 生成chat_id
        cid = self.server.gen_chat_id(user.get_username())
        chat = data.Chat(cid, base64.b64decode(
            request.args.get('title')).decode('utf-8'))
        user.add_chat(chat)
        return json.dumps(cid), 200

    def chat_get(self):
        """
        获取会话内容.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        chat = self.server.get_chat(user, base64.b64decode(
            request.args.get('cid')).decode('utf-8'))
        if chat is None:
            return json.dumps('invalid_chat_id'), 200
        return json.dumps(chat, default=lambda o: o._to_db_dict(o)), 200

    def chat_del(self):
        """
        删除会话.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        chat = self.server.get_chat(user, base64.b64decode(
            request.args.get('cid')).decode('utf-8'))
        if chat is None:
            return json.dumps('invalid_chat_id'), 403
        user.del_chat(chat.get_chat_id())
        return json.dumps('success'), 200

    def chat_gen(self):
        """
        生成聊天内容.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        chat = self.server.get_chat(user, base64.b64decode(
            request.args.get('cid')).decode('utf-8'))
        if chat is None:
            return json.dumps('invalid_chat_id'), 403
        prompt = base64.b64decode(request.args.get('p')).decode('utf-8')
        if prompt is None:
            return json.dumps('invalid_prompt'), 403
        provider_models = json.loads(base64.b64decode(
            request.args.get('provider_models')).decode('utf-8'))
        send_msg = data.Message('user', user.get_username(), prompt)
        chat.add_msg(send_msg)
        responses = Api.get_responses(chat, provider_models, user.get_api_dict())
        print(responses)
        for response in responses:
            recv_msg = data.Message('assistant', response['model'], response['message'], response['code'])
            chat.add_recv_msg(response['model'], recv_msg)
        recv_msg_list = chat.get_recv_msg_tmp()
        if len(responses) == 1:
            chat.sel_recv_msg(responses[0]['model'])
        user.add_chat(chat)
        return json.dumps(recv_msg_list, default=lambda o: o.__dict__()), 200

    def chat_gen_stream(self):
        '''
        生成聊天内容流.
        '''
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        chat = self.server.get_chat(user, base64.b64decode(
            request.args.get('cid')).decode('utf-8'))
        if chat is None:
            return json.dumps('invalid_chat_id'), 403
        prompt = base64.b64decode(request.args.get('p')).decode('utf-8')
        if prompt is None:
            return json.dumps('invalid_prompt'), 403
        provider_models = json.loads(base64.b64decode(
            request.args.get('provider_models')).decode('utf-8'))
        send_msg = data.Message('user', user.get_username(), prompt)
        chat.add_msg(send_msg)
        stream = Api.get_responses_stream(chat, provider_models, user.get_api_dict())

        def res():
            responses = {}
            for chunk in stream:            
                yield json.dumps(chunk, default=lambda o: o.__dict__())+'\n'
                
                if chunk['model'] not in responses:
                    responses[chunk['model']] = {
                        "message": "",
                        "codes": []
                    }
                
                responses[chunk['model']]["codes"].append(chunk['code'])
                responses[chunk['model']]["message"] += chunk['message']

            # 保存流
            print(responses)
            for model in responses:
                recv_msg = data.Message('assistant', model, responses[model]["message"], responses[model]["codes"])
                chat.add_recv_msg(model, recv_msg)
            user.add_chat(chat)
            if len(responses) == 1:
                chat.sel_recv_msg(list(responses.keys())[0])
        headers = {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
        }
        return Response(res(), 200, headers=headers)


    def chat_sel(self):
        """
        选择答复.
        """
        user = self.server.get_user(session.get('username'), session.get('session_id'))
        if user is None:
            return json.dumps('invalid_user'), 403
        chat = self.server.get_chat(user, base64.b64decode(
            request.args.get('cid')).decode('utf-8'))
        if chat is None:
            return json.dumps('invalid_chat_id'), 403
        model_name = base64.b64decode(request.args.get('name')).decode('utf-8')
        if model_name not in chat.get_recv_msg_tmp():
            return json.dumps('invalid_model_name'), 200
        chat.sel_recv_msg(model_name)
        return json.dumps('success'), 200

ws = WebSever()
app = ws.app
if __name__ == '__main__':
    # 启动服务器
    ws = WebSever()
    ws.run(debug=True)