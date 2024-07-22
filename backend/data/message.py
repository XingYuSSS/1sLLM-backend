class Message:
    """
    存储一条消息.
    """

    def __init__(self, role=None, name=None, msg=None, code=None):
        self.role = role
        self.name = name
        self.msg = msg
        self.code = code

    def __dict__(self):
        return Message._to_db_dict(self)
    
    def to_role_dict(self):
        return {'role': self.role, 'content': self.msg}
    
    def _to_db_dict(self) -> dict:
        '''
        将对象转换为可保存至mongodb的字典.
        '''
        return {
            'role': self.role,
            'name': self.name,
            'msg': self.msg,
            'code': self.code
        }
    
    @staticmethod
    def _from_db_dict(db_dict: dict) -> None:
        '''
        从mongodb的字典中恢复对象.
        '''
        role = db_dict['role']
        name = db_dict['name']
        msg = db_dict['msg']
        code = db_dict['code']
        
        return Message(role, name, msg, code)