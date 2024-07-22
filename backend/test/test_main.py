import pytest
import base64
import hashlib
import json
from flask import session
from main import WebSever  # 假设你的类文件名为 webserver.py
from data import Server, User, Chat, Message

@pytest.fixture
def client():
    app = WebSever().app
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            # 初始化数据库或服务器
            client.server = Server()
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 302  # 重定向到 index.html

def test_user_exist(client):
    username = base64.b64encode('testuser'.encode('utf-8')).decode('utf-8')
    client.server.add_user(User(username='testuser'))  # 预先添加用户
    response = client.get(f'/user/exist?user={username}')
    assert response.text == '"user_name_exist"'

def test_user_register(client):
    username = base64.b64encode('newuser'.encode('utf-8')).decode('utf-8')
    password = base64.b64encode('newpassword'.encode('utf-8')).decode('utf-8')
    response = client.get(f'/user/register?user={username}&pd={password}')
    assert client.server.check_user_name_exist('newuser')
    # assert response.text == '"success"'
    

def test_user_login(client):
    username = base64.b64encode('loginuser'.encode('utf-8')).decode('utf-8')
    password = base64.b64encode('loginpassword'.encode('utf-8')).decode('utf-8')
    password_md5 = hashlib.md5('loginpassword'.encode('utf-8')).hexdigest()
    client.server.add_user(User('loginuser', password_md5))  # 预先添加用户
    response = client.get(f'/user/login?user={username}&pd={password}')
    # assert response.json == 'success'
    assert session['username'] == 'loginuser'

# def test_user_logout(client):
#     with client.session_transaction() as sess:
#         sess['username'] = 'logoutuser'
#         sess['session_id'] = 'sessid123'
#     response = client.get('/user/logout')
#     # assert response.json == 'success'
#     assert 'username' not in session

# def test_api_providers(client):
#     response = client.get('/api/providers')
#     assert response.status_code == 200
#     assert isinstance(response.json, list)  # 根据你预期的返回类型进行断言

# def test_api_models(client):
#     with client.session_transaction() as sess:
#         sess['username'] = 'modeluser'
#         sess['session_id'] = 'sessid123'
#     client.server.add_user(User('modeluser', 'password'))  # 预先添加用户
#     response = client.get('/api/models')
#     assert response.status_code == 200
#     assert isinstance(response.json, dict)  # 根据你预期的返回类型进行断言

# def test_chat_new(client):
#     # 将密码哈希处理
#     password_md5 = hashlib.md5('123456'.encode('utf-8')).hexdigest()
#     client.server.add_user(User('admin', password_md5))  # 预先添加用户

#     # 模拟用户登录
#     with client.session_transaction() as sess:
#         sess['username'] = 'admin'
#         sess['session_id'] = client.server.gen_session_id('admin')
    
#     client.server.set_session_dict('admin', sess['session_id'])

#     # 发起新建会话请求
#     response = client.get('/chat/new')
    
#     # 验证响应状态码
#     assert response.status_code == 200
    
#     # 验证响应数据类型
#     assert isinstance(response.text, str)  # 返回新的chat_id
    
#     # 验证响应数据内容（chat_id的长度或格式，根据实际需求调整）
#     chat_id = response.text
#     assert len(chat_id) > 0  # 假设chat_id不为空

#     # 验证会话是否已添加到用户数据中
#     user = client.server.get_user('admin', sess['session_id'])
#     assert chat_id in user.get_chat_dict()


# # 继续为其他端点编写测试
# # ...
