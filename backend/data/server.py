import hashlib
import random
import time
from .chat import Chat
from .user import User
from pymongo import MongoClient
from dotenv import load_dotenv
import os

class Server:
    """
    服务器所需的一切信息.
    属性:
        user_dict: 用户名-User
        session_dict: 用户名-session_id, 用于记录会话信息
    """

    def __init__(self):
        self._user_dict = {}
        self._session_dict = {}

        # 从数据库中加载数据
        self.load_data_from_db()
        
    def load_data_from_db(self):
        """
        从数据库中加载数据.
        """
        # 连接数据库
        load_dotenv()
        username = os.getenv('MONGO_USERNAME')
        password = os.getenv('MONGO_PASSWORD')
        host = os.getenv('MONGO_HOST')
        port = os.getenv('MONGO_PORT')
        if username == '' or password == '':
            uri = f"mongodb://{host}:{port}"
        else:
            uri = f"mongodb://{username}:{password}@{host}:{port}"
        print(uri)
        client = MongoClient(uri)
        db = client['1sLLM']
        cursor = db['user'].find({})
        for raw_user_data in cursor:
            user_data = User._from_db_dict(raw_user_data)
            user = User(**user_data, tmp=True)
            self._user_dict[user.get_username()] = user
        client.close()


    def add_user(self, user : User):
        """
        添加用户.
        """
        self._user_dict[user.get_username()] = user

    def gen_chat_id(self, username):
        """
        生成chat_id.
        """
        txt = username + time.strftime('%Y_%m_%d_%H_%M_%S',
                                       time.localtime()) + str(random.randint(0, 100))
        cid = hashlib.md5(txt.encode('utf-8')).hexdigest()
        return cid

    def gen_session_id(self, username):
        """
        生成session_id.
        """
        txt = username + str(time.time())
        sid = hashlib.md5(txt.encode('utf-8')).hexdigest()
        return sid

    def get_chat(self, user : User, cid) -> Chat:
        """
        获取chat.
        """
        chat = user.get_chat(cid)
        if chat is None:
            return None
        return chat

    def get_user(self, uname, sid) -> User:
        """
        检查session_id.
        """
        print(uname, sid)
        if uname is None or sid is None:
            return None
        if self._session_dict.get(uname) == sid:
            return self._user_dict[uname]
        return None

    def check_user_name_exist(self, uname):
        """
        检查用户名是否存在.
        """
        return uname in self._user_dict
    
    def get_password_md5(self, uname):
        """
        获取用户密码的md5.
        """
        return self._user_dict[uname].get_password()
    
    def set_session_dict(self, key, value):
        """
        设置session_dict.
        """
        self._session_dict[key] = value

    def pop_session_dict(self, key):
        """
        删除session_dict.
        """
        self._session_dict.pop(key, None)