import base64
import hashlib
import json
import data
from api.base import Api
from flask import Flask, request, session, redirect, Response
from flask_cors import CORS
import socketio
import time

class WebSever:
    def __init__(self):
        self.app = Flask(__name__, static_folder='static', static_url_path='')
        CORS(self.app, supports_credentials=True)
        self.server = data.Server()
        self.socket_server = Api.get_socket_server()
        self.app.secret_key = '123456'

        # 未登录可用
        self.app.add_url_rule('/', view_func=self.index)
        self.app.add_url_rule('/api/providers', view_func=self.api_providers)
        self.app.add_url_rule('/user/exist', view_func=self.user_exist)
        self.app.add_url_rule('/user/register', view_func=self.user_register)
        self.app.add_url_rule('/user/login', view_func=self.user_login)
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
        password = base64.b64decode(request.args.get('pd')).decode('utf-8')
        password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        user = data.User(username, password_md5)
        self.server.add_user(user)
        return json.dumps('success'), 200

    def user_login(self):
        """
        登录.
        """
        username = base64.b64decode(request.args.get('user')).decode('utf-8')
        password = base64.b64decode(request.args.get('pd')).decode('utf-8')
        if username is None or password is None:
            return json.dumps('invalid_username_or_password'), 401
        password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        # 检查用户名密码
        print(f'Login: {username}, {password}')
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
        # 保存流
        print(stream)
        responses = {}
        for chunk in stream:
            print(chunk)
            if chunk['model'] not in responses:
                responses[chunk['model']] = {}
                responses[chunk['model']]["message"] = ""
                responses[chunk['model']]["codes"] = []
            responses[chunk['model']]["codes"].append(chunk['code'])
            responses[chunk['model']]["message"] += chunk['message']
        # print(responses)
        for model_name, response in responses.items():
            recv_msg = data.Message('assistant', model_name, response['message'], all(response['codes']))
            chat.add_recv_msg(model_name, recv_msg)
        # TODO: 选择答复
        if len(responses) == 1:
            chat.sel_recv_msg(list(responses.keys())[0])
        user.add_chat(chat)
        return Response(stream, 200)

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

if __name__ == '__main__':
    # 启动服务器
    ws = WebSever()
    ws.run(debug=True)