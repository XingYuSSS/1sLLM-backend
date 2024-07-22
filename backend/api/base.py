from concurrent.futures import ThreadPoolExecutor
import importlib
import pkgutil

class LockAndSubclassTrackingMeta(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._subclasses = []

        for base in bases:
            if hasattr(base, '_subclasses'):
                base._subclasses.append(cls)

        for key, value in dct.items():
            if callable(value) and getattr(value, "_locked", False):
                setattr(cls, key, cls._create_locked_method(value))

    def _create_locked_method(cls, method):
        """创建一个锁定的方法，防止子类覆盖或调用"""
        def locked_method(self, *args, **kwargs):
            if type(self) != cls:
                raise TypeError(f"Method '{method.__name__}' is locked and cannot be overridden or called by subclasses.")
            return method(self, *args, **kwargs)
        return locked_method

    def all_subclasses(cls):
        all_subs = set(cls._subclasses)
        for subclass in cls._subclasses:
            all_subs.update(subclass.all_subclasses())
        return all_subs

def locked_method(func):
    """装饰器，用于标记需要锁定的方法"""
    func._locked = True
    return func

class Api(metaclass=LockAndSubclassTrackingMeta):
    """
    存储api信息的基类.
    """
    def __init__(self, api_key=None) -> None:
        self.api_key = api_key
        self.supported_models = self._list_models()
    
    @staticmethod
    @locked_method
    def get_providers():
        supported_service_providers = Api._get_supported_service_providers()
        return supported_service_providers

    @staticmethod
    @locked_method
    def _get_supported_service_providers():
        """
        查看支持哪些服务商.
        """
        all_subclasses = Api.all_subclasses()
        supported_service_providers = [cls.__name__.replace('_Api', '') for cls in all_subclasses]
        return supported_service_providers
    
    @staticmethod
    def get_responses(chat, provider_models, provider_keys):
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(Api._get_responses, chat, provider, model_list, provider_keys.get(provider, '')) for provider, model_list in provider_models.items()]

        res = [f.result() for f in futures]
        
        result = []
        for sub_res in res:
            result.extend(sub_res)
        return result
    
    @staticmethod
    def _get_responses(chat, provider: str, model_list, api_key):
        if provider not in Api.get_providers():
            raise ValueError(f"Provider '{provider}' is not supported.")

        a = getattr(importlib.import_module(f'api.{provider.lower()}'), f'{provider}_Api')
        print(a)
        api = a(api_key)

        supported_models = api.supported_models
        if any(model not in supported_models for model in model_list):
            raise ValueError(f"Model '{model_list}' is not supported by provider '{provider}'.")
        
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(api._get_response, chat, model_id) for model_id in model_list]
        
        res = [f.result() for f in futures]
        return res
    
    @staticmethod
    def get_socket_server():
        if "Scir" in Api.get_providers():
            return importlib.import_module('api.scir').Scir_Api.server

    def _list_models(self):
        """
        获取模型列表. 动态向服务商获取.
        """
        raise NotImplementedError("Subclasses should implement this method.")
    
    def _get_response(self, chat, model_list, api_key):
        """
        获取model_list的回复.
        """
        raise NotImplementedError("Subclasses should implement this method.")


# 自动导入子类模块
def import_submodules(package_name):
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package_name}.{module_name}")

import_submodules('api')
import sys
mo = [m for m in sys.modules.keys()]
print('api.qwen' in mo)
