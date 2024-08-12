from concurrent.futures import ThreadPoolExecutor
import importlib
import pkgutil
import itertools

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
    def get_responses_stream(chat, provider_models, provider_keys):
        streams = []
        for provider, model_list in provider_models.items():
            streams.extend(Api._get_responses_stream(chat, provider, model_list, provider_keys.get(provider, '')))
        merged_stream = merge_iterators(streams)
        yield from merged_stream
        
    @staticmethod
    def _get_responses_stream(chat, provider: str, model_list, api_key):
        if provider not in Api.get_providers():
            raise ValueError(f"Provider '{provider}' is not supported.")

        a = getattr(importlib.import_module(f'api.{provider.lower()}'), f'{provider}_Api')
        api = a(api_key)

        supported_models = api.supported_models
        if any(model not in supported_models for model in model_list):
            raise ValueError(f"Model '{model_list}' is not supported by provider '{provider}'.")
        
        iterators = []
        for model_id in model_list:
            iterator = api._get_response_stream(chat, model_id)
            iterators.append(iterator)
        return iterators

    @staticmethod
    def get_socket_server():
        if "Scir_socket" in Api.get_providers():
            return importlib.import_module('api.scir_socket').Scir_socket_Api.server

    def _list_models(self):
        """
        获取模型列表. 动态向服务商获取.
        """
        raise NotImplementedError("Subclasses should implement this method.")
    
    def _get_response(self, chat, model_id):
        """
        获取model_id的回复.
        """
        raise NotImplementedError("Subclasses should implement this method.")
    
    def _get_response_stream(self, chat, model_id):
        """
        获取model_id的回复流.
        """
        raise NotImplementedError("Subclasses should implement this method.")

def merge_iterators(iterables):
    """
    Merge multiple iterables into a single iterator, preserving all elements from each iterable.
    Each item in the output will be a dictionary with the source iterable's index and the value.
    
    Args:
        iterables (list): A list of iterables to be merged.
        
    Returns:
        iterator: An iterator that yields dictionaries with 'index' and 'value' keys.
    """
    # Define a sentinel value that isn't expected to occur in any of the iterables.
    sentinel = object()
    
    # Use zip_longest to iterate over all iterables, filling short ones with the sentinel.
    for items in itertools.zip_longest(*iterables, fillvalue=sentinel):
        # Filter out the sentinel and yield the rest as dictionaries.
        yield from (item for item in items if item is not sentinel)

# 自动导入子类模块
def import_submodules(package_name):
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package_name}.{module_name}")

import_submodules('api')
import sys
mo = [m for m in sys.modules.keys()]
print('api.qwen' in mo)
