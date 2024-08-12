from typing import Any
import pymongo
from dotenv import load_dotenv
import os

class DB:
    load_dotenv()
    username = os.getenv('MONGO_USERNAME')
    password = os.getenv('MONGO_PASSWORD')
    host = os.getenv('MONGO_HOST')
    port = os.getenv('MONGO_PORT')
    uri = f"mongodb://{username}:{password}@{host}:{port}"
    db = pymongo.MongoClient(uri)['1sLLM']
    
    def __init__(self, set_name=None, db_id=None, db_dict=None, tmp=False) -> None:
        if set_name is None:
            raise ValueError("set_name must be provided.")
        self.db_set = DB.db[set_name]
        self._db_id = db_id
        if not tmp:
            for key, value in db_dict.items():
                self.update(key, value)

    @staticmethod
    def _to_db_dict() -> dict:
        '''
        将对象转换为可保存至mongodb的字典.
        '''
        raise NotImplementedError
    
    @staticmethod
    def _from_db_dict(db_dict: dict) -> dict:
        '''
        从mongodb的字典中重构字典.
        '''
        raise NotImplementedError
    
    def update(self, key: str, value: Any) -> None:
        '''
        直接同步至数据库，不更新self.
        '''
        self.db_set.update_one({'_id': self._db_id}, {'$set': {key: value}}, upsert=True)        

    def delete(self) -> None:
        '''
        从数据库中删除对象.
        '''
        self.db_set.delete_one({'_id': self._db_id})
    
    def get(self, key: str) -> Any:
        '''
        从数据库中获取属性.
        '''
        db_dict = self.db_set.find_one({'_id': self._db_id})
        obj_dict = self._from_db_dict(db_dict)
        return obj_dict[key]