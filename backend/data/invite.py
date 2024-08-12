import random
import string
from pymongo import MongoClient
from dotenv import load_dotenv
import os

class InviteCodeManager:
    def __init__(self, db_name='1sLLM', collection_name='invite_codes', default_length=8):
        load_dotenv()
        username = os.getenv('MONGO_USERNAME')
        password = os.getenv('MONGO_PASSWORD')
        host = os.getenv('MONGO_HOST')
        port = os.getenv('MONGO_PORT')
        uri = f"mongodb://{username}:{password}@{host}:{port}"

        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.default_length = default_length
        self.collection.create_index('code', unique=True)
    
    def __generate_code(self, length=None):
        if length is None:
            length = self.default_length
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not self.collection.find_one({"code": code}):
                invite_data = {
                    "code": code,
                    "used": False
                }
                try:
                    self.collection.insert_one(invite_data)
                    return code
                except Exception as e:
                    print(f"Error inserting code: {e}")
                    return None
    
    def get_dynamic_invite_codes(self, quantity, length=None):
        codes = []
        for _ in range(quantity):
            code = self.__generate_code(length)
            if code:
                codes.append(code)
        return codes
    
    def validate_code(self, code):
        '''验证邀请码是否有效且未使用
        返回值：
        0 - 无效邀请码
        -1 - 有效但已使用
        1 - 有效且未使用
        '''
        invite = self.collection.find_one({"code": code})
        if invite is None:
            return 0
        elif invite["used"]:
            return -1
        else:
            return 1
    
    def mark_code_as_used(self, code):
        result = self.collection.update_one({"code": code, "used": False}, {"$set": {"used": True}})
        return result.modified_count > 0
    
    def __delete_code(self, code):
        result = self.collection.delete_one({"code": code})
        return result.deleted_count > 0
    
    def delete_codes_batch(self, quantity):
        unused_codes = self.collection.find({"used": False}).limit(quantity)
        deleted_codes = []
        for code in unused_codes:
            if self.__delete_code(code["code"]):
                deleted_codes.append(code["code"])
        return deleted_codes
    
    def list_codes(self):
        return list(self.collection.find())

def menu():
    print("\n邀请码管理系统")
    print("1. 获取邀请码")
    print("2. 验证邀请码")
    print("3. 标记邀请码为已使用")
    print("4. 批量删除未使用的邀请码")
    print("5. 列出所有邀请码")
    print("6. 退出")

def main():
    manager = InviteCodeManager()
    
    while True:
        menu()
        choice = input("请选择操作: ")
        
        if choice == '1':
            quantity = int(input("请输入要生成的邀请码数量: "))
            length = input(f"请输入邀请码长度（默认为{manager.default_length}位）: ")
            length = int(length) if length else None
            codes = manager.get_dynamic_invite_codes(quantity, length)
            print(f"生成并返回的邀请码: {codes}")
        
        elif choice == '2':
            code = input("请输入要验证的邀请码: ")
            is_valid = manager.validate_code(code)
            if is_valid == 1:
                print("该邀请码有效且未使用。")
            elif is_valid == -1:
                print("该邀请码有效但已使用。")
            else:
                print("该邀请码无效。")
        
        elif choice == '3':
            code = input("请输入要标记为已使用的邀请码: ")
            if manager.mark_code_as_used(code):
                print(f"邀请码 {code} 已被标记为已使用。")
            else:
                print(f"无法标记邀请码 {code} 为已使用。可能邀请码无效或已被使用。")
        
        elif choice == '4':
            quantity = int(input("请输入要删除的邀请码数量: "))
            deleted_codes = manager.delete_codes_batch(quantity)
            print(f"已删除的邀请码: {deleted_codes}")
        
        elif choice == '5':
            codes = manager.list_codes()
            if codes:
                print("所有邀请码:")
                for c in codes:
                    status = "已使用" if c["used"] else "未使用"
                    print(f"邀请码: {c['code']} - 状态: {status}")
            else:
                print("没有邀请码。")
        
        elif choice == '6':
            print("退出系统。")
            break
        
        else:
            print("无效的选择，请重新选择。")

if __name__ == "__main__":
    main()
