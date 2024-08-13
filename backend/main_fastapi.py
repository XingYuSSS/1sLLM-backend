import base64
import hashlib
import json
import random
import re

from fastapi.staticfiles import StaticFiles
import data
from api.base import Api
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, StreamingResponse
from dotenv import load_dotenv
import os
import time
from pydantic import BaseModel
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.sms.v20210111 import sms_client, models

class WebServer:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self.server = data.Server()
        self.socket_server = Api.get_socket_server()
        self.invite_code_manager = data.InviteCodeManager()
        self.app.add_middleware(SessionMiddleware, secret_key=os.getenv('BACKEND_SECRET_KEY'))

        load_dotenv()
        self.TencentConfig = {
            "SecretId": os.getenv('TENCENT_SECRET_ID'),
            "SecretKey": os.getenv('TENCENT_SECRET_KEY'),
            "TemplateId": os.getenv('TENCENT_TEMPLATE_ID'),
            "SignName": os.getenv('TENCENT_SIGN_NAME'),
            "SmsSdkAppId": os.getenv('TENCENT_SMS_SDK_APP_ID')
        }
        self.tmp_sms_code = {}

        # 注册路由
        self.app.get("/")(self.index)
        self.app.get("/api/providers")(self.api_providers)
        self.app.get("/user/exist")(self.user_exist)
        self.app.get("/user/register")(self.user_register)
        self.app.get("/user/login")(self.user_login)
        self.app.get("/sms/code")(self.sms_code_get)
        self.app.get("/user/logout")(self.user_logout)
        self.app.get("/api/models")(self.api_models)
        self.app.get("/api/list")(self.api_list)
        self.app.get("/api/add")(self.api_add)
        self.app.get("/api/del")(self.api_del)
        self.app.get("/chat/list")(self.chat_list)
        self.app.get("/chat/new")(self.chat_new)
        self.app.get("/chat/get")(self.chat_get)
        self.app.get("/chat/title")(self.chat_title)
        self.app.get("/chat/del")(self.chat_del)
        self.app.get("/chat/gen")(self.chat_gen)
        self.app.get("/chat/gen/stream")(self.chat_gen_stream)
        self.app.get("/chat/sel")(self.chat_sel)

        if self.socket_server is not None:
            # FastAPI 不支持 WSGI，你可能需要使用 Uvicorn 或其他 ASGI 服务器
            pass

    async def index(self):
        """
        主页.
        """
        return RedirectResponse(url='/static/index.html')

    async def user_exist(self, request: Request):
        """
        检查用户是否存在.
        """
        username = base64.b64decode(request.query_params.get('user')).decode('utf-8')
        if self.server.check_user_name_exist(username):
            return JSONResponse(content='user_name_exist', status_code=200)
        return JSONResponse(content='user_name_not_exist', status_code=200)

    async def user_register(self, request: Request):
        """
        注册.
        """
        params = request.query_params
        username = base64.b64decode(params.get('user')).decode('utf-8')
        if self.server.check_user_name_exist(username):
            return JSONResponse(content='user_name_exist', status_code=200)
        invite_code = base64.b64decode(params.get('ic')).decode('utf-8')
        validation = self.invite_code_manager.validate_code(invite_code)
        if validation == 0:
            return JSONResponse(content='invalid_invite_code', status_code=200)
        elif validation == -1:
            return JSONResponse(content='used_invite_code', status_code=200)
        else:
            self.invite_code_manager.mark_code_as_used(invite_code)
        sms_code = base64.b64decode(params.get('sc')).decode('utf-8')
        phone = base64.b64decode(params.get('phone')).decode('utf-8')
        if sms_code != self.tmp_sms_code.get(phone):
            return JSONResponse(content='invalid_sms_code', status_code=200)
        del self.tmp_sms_code[phone]
        password = base64.b64decode(params.get('pd')).decode('utf-8')
        password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        user = data.User(username, password_md5, phone)
        self.server.add_user(user)
        return JSONResponse(content='success', status_code=200)

    async def user_login(self, request: Request):
        """
        登录.
        """
        params = request.query_params
        username = base64.b64decode(params.get('user')).decode('utf-8')
        password = base64.b64decode(params.get('pd')).decode('utf-8')
        if username is None or password is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_username_or_password")
        password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
        if not self.server.check_user_name_exist(username):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_username_or_password")
        if self.server.get_password_md5(username) != password_md5:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_username_or_password")
        sid = self.server.gen_session_id(username)
        self.server.set_session_dict(username, sid)
        request.session.update({'username': username, 'session_id': sid})
        return JSONResponse(content={'success': True, 'session_id': sid}, status_code=200)

    async def user_logout(self, request: Request):
        """
        登出.
        """
        username = request.session.get('username')
        if username is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_username")
        request.session.clear()
        self.server.pop_session_dict(username)
        return JSONResponse(content='success', status_code=200)

    async def sms_code_get(self, request: Request):
        """
        获取短信验证码.
        """
        phone = base64.b64decode(request.query_params.get('phone')).decode('utf-8')
        if not re.match(r'^1[3456789]\d{9}$', phone):
            return JSONResponse(content='invalid_phone', status_code=200)
        sms_code = str(random.randint(100000, 999999))
        # TODO: 发送短信
        while True:
            try:
                cred = credential.Credential(self.TencentConfig["SecretId"], self.TencentConfig["SecretKey"])
                httpProfile = HttpProfile()
                httpProfile.endpoint = "sms.tencentcloudapi.com"
                clientProfile = ClientProfile()
                clientProfile.httpProfile = httpProfile
                client = sms_client.SmsClient(cred, "ap-beijing", clientProfile)

                req = models.SendSmsRequest()
                params = {
                    "PhoneNumberSet": [phone],
                    "SmsSdkAppId": self.TencentConfig["SmsSdkAppId"],
                    "TemplateId": self.TencentConfig["TemplateId"],
                    "SignName": self.TencentConfig["SignName"],
                    "TemplateParamSet.N": [sms_code]
                }
                req.from_json_string(json.dumps(params))

                resp = client.SendSms(req)
                print(resp.to_json_string())
                break

            except TencentCloudSDKException as err:
                print(err)
                time.sleep(1)

        self.tmp_sms_code[phone] = sms_code
        return JSONResponse(content='success', status_code=200)

    async def api_providers(self):
        """
        获取全局支持的服务商.
        """
        return JSONResponse(content=Api.get_providers(), status_code=200)

    async def api_models(self, request: Request):
        """
        获取用户可用的{服务商: 模型列表}.
        """
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        user.refresh_model('Scir')
        models = user.get_available_models()
        return JSONResponse(content=models, status_code=200)

    async def api_list(self, request: Request):
        """
        获取api列表.
        """
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        return JSONResponse(content=user.get_api_list(), status_code=200)

    async def api_add(self, request: Request):
        """
        添加api.
        """
        params = request.query_params
        service_provider_name = base64.b64decode(params.get('name')).decode('utf-8')
        api_key = base64.b64decode(params.get('key')).decode('utf-8')
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        if not user.add_api(service_provider_name, api_key):
            return JSONResponse(content='invalid_service_provider_name_or_key', status_code=200)
        return JSONResponse(content='success', status_code=200)

    async def api_del(self, request: Request):
        """
        删除api.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        service_provider_name = params.get('name')
        if service_provider_name is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_service_provider_name")
        user.del_api(service_provider_name)
        return JSONResponse(content='success', status_code=200)

    async def chat_list(self, request: Request):
        """
        获取聊天记录列表.
        """
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        response = {k: v._to_db_dict(v) for k,v in user.get_chat_dict().items()}
        return JSONResponse(content=response, status_code=200)

    async def chat_new(self, request: Request):
        """
        新建聊天记录.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        cid = self.server.gen_chat_id(user.get_username())
        chat = data.Chat(cid, base64.b64decode(params.get('title')).decode('utf-8'))
        user.add_chat(chat)
        return JSONResponse(cid, status_code=200)

    async def chat_get(self, request: Request):
        """
        获取聊天记录.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        cid = params.get('cid')
        chat = self.server.get_chat(user, base64.b64decode(cid).decode('utf-8'))
        if chat is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_chat_id")
        response = chat._to_db_dict(chat)
        return JSONResponse(content=response, status_code=200)

    async def chat_title(self, request: Request):
        """
        更新聊天记录标题.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        chat = self.server.get_chat(user, base64.b64decode(params.get('cid')).decode('utf-8'))
        if chat is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_chat_id")
        title = base64.b64decode(params.get('title')).decode('utf-8')
        chat.set_title(title)
        return JSONResponse(content='success', status_code=200)

    async def chat_del(self, request: Request):
        """
        删除聊天记录.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        chat = self.server.get_chat(user, base64.b64decode(params.get('cid')).decode('utf-8'))
        if chat is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_chat_id")
        user.del_chat(chat.get_chat_id())
        return JSONResponse(content='success', status_code=200)

    async def chat_gen(self, request: Request):
        """
        生成聊天回复.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        chat = self.server.get_chat(user, base64.b64decode(params.get('cid')).decode('utf-8'))
        if chat is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_chat_id")
        prompt = base64.b64decode(params.get('p')).decode('utf-8')
        if prompt is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_prompt")
        provider_models = json.loads(base64.b64decode(params.get('provider_models')).decode('utf-8'))
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
        response = {k: v.__dict__() for k, v in recv_msg_list.items()}
        return JSONResponse(content=response, status_code=200)

    async def chat_gen_stream(self, request: Request):
        """
        流式生成聊天回复.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        chat = self.server.get_chat(user, base64.b64decode(params.get('cid')).decode('utf-8'))
        if chat is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_chat_id")
        prompt = base64.b64decode(params.get('p')).decode('utf-8')
        if prompt is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_prompt")
        provider_models = json.loads(base64.b64decode(params.get('provider_models')).decode('utf-8'))
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
        return StreamingResponse(res(), 200)
    
    async def chat_sel(self, request: Request):
        """
        选择聊天.
        """
        params = request.query_params
        user = self.server.get_user(request.session.get('username'), request.session.get('session_id'))
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_user")
        chat = self.server.get_chat(user, base64.b64decode(params.get('cid')).decode('utf-8'))
        if chat is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_chat_id")
        model_name = base64.b64decode(params.get('name')).decode('utf-8')
        if model_name not in chat.get_recv_msg_tmp():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_model_name")
        chat.sel_recv_msg(model_name)
        return JSONResponse(content='success', status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(WebServer().app, host="0.0.0.0", port=8000)