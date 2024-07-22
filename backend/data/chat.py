from .db import DB
from .message import Message

class Chat(DB):
    """
    存储一次会话.
    属性:
        msg_list: 消息列表
        recv_msg_tmp: 模型名-Msg, 最后一次回答的接收消息
    """

    def __init__(self, cid=None, title=None, msg_list=[], recv_msg_tmp={}, tmp=False):
        super().__init__(
            set_name='chat',
            db_id=cid,
            db_dict={
                'chat_id': cid,
                'chat_title': title,
                'msg_list': msg_list,
                'recv_msg_tmp': recv_msg_tmp
            },
            tmp=tmp
        )

    @staticmethod
    def _to_db_dict(obj) -> dict:
        '''
        将对象转换为可保存至mongodb的字典.
        '''
        return {
            'chat_id': obj.get_chat_id(),
            'chat_title': obj.get_chat_title(),
            'msg_list': [msg._to_db_dict() for msg in obj.get_msg_list()],
            'recv_msg_tmp': {model_name: msg._to_db_dict() for model_name, msg in obj.get_recv_msg_tmp().items()}
        }
    
    @staticmethod
    def _from_db_dict(db_dict: dict) -> None:
        chat_id = db_dict['chat_id']
        chat_title = db_dict['chat_title']
        msg_list = [Message._from_db_dict(msg) for msg in db_dict['msg_list']]
        recv_msg_tmp = {model_name: Message._from_db_dict(msg) for model_name, msg in db_dict['recv_msg_tmp'].items()}
        
        return {
            'chat_id': chat_id,
            'chat_title': chat_title,
            'msg_list': msg_list,
            'recv_msg_tmp': recv_msg_tmp
        }
    
    def __dict__(self):
        return Chat._to_db_dict(self)
    
    @staticmethod
    def rebuilt_from_dict(dict, tmp):
        '''
        重构对象.
        tmp: 是否为临时对象.
        '''
        return Chat(
            cid=dict['chat_id'],
            title=dict['chat_title'],
            msg_list=dict['msg_list'],
            recv_msg_tmp=dict['recv_msg_tmp'],
            tmp=tmp
        )

    def get_chat_id(self):
        return self.get('chat_id')

    def get_chat_title(self):
        return self.get('chat_title')

    def get_msg_list(self):
        return self.get('msg_list')

    def get_recv_msg_tmp(self):
        return self.get('recv_msg_tmp')

    def set_title(self, title):
        self.update('chat_title', title)

    def add_msg(self, msg):
        current_msg_list = self.get_msg_list()
        current_msg_list.append(msg)
        current_msg_list = [msg._to_db_dict() for msg in current_msg_list]
        self.update('msg_list', current_msg_list)

    def add_recv_msg(self, model_name, msg):
        current_recv_msg_tmp = self.get_recv_msg_tmp()
        current_recv_msg_tmp[model_name] = msg
        current_recv_msg_tmp = {model_name: msg._to_db_dict() for model_name, msg in current_recv_msg_tmp.items()}
        self.update('recv_msg_tmp', current_recv_msg_tmp)

    def sel_recv_msg(self, model_name):
        current_recv_msg_tmp = self.get_recv_msg_tmp()
        current_msg_list = self.get_msg_list()
        current_msg_list.append(current_recv_msg_tmp[model_name])
        current_msg_list = [msg._to_db_dict() for msg in current_msg_list]
        self.update('msg_list', current_msg_list)
        self.update('recv_msg_tmp', {})
