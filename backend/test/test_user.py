import pytest
from data import User, Chat, Message

# @pytest.fixture
# def setup_user():
#     # Create a new user instance
#     user = User(username='user001', password='password123')
#     return user

# def test_user_initialization(setup_user):
#     user = setup_user
#     assert user.get_username() == 'user001'
#     assert user.get_password() == 'password123'
#     assert user.get_api_dict() == {}
#     assert user.get_chat_dict() == {}
#     assert user.get_available_models() == {}

# def test_add_chat(setup_user):
#     user = setup_user

#     # Create a chat instance
#     chat = Chat(cid='chat001', title='Test Chat', msg_list=[Message(role='user', name='Alice', msg='Hello!', code='001'), Message(role='bot', name='Bot1', msg='Hi there!', code='002')], recv_msg_tmp={'BotModel1': Message(role='bot', name='Bot1', msg='Hi there!', code='002')})

#     # Add the chat to the user
#     user.add_chat(chat)

#     # Check if the chat is added correctly
#     chat_dict = user.get_chat_dict()
#     assert 'chat001' in chat_dict
#     added_chat = chat_dict['chat001']
#     assert added_chat['chat_id'] == 'chat001'
#     assert added_chat['chat_title'] == 'Test Chat'

# def test_del_chat(setup_user):
#     user = setup_user

#     # Create a chat instance
#     chat = Chat(cid='chat001', title='Test Chat')

#     # Add the chat to the user
#     user.add_chat(chat)

#     # Delete the chat from the user
#     user.del_chat('chat001')

#     # Check if the chat is deleted correctly
#     chat_dict = user.get_chat_dict()
#     assert 'chat001' not in chat_dict

# def test_add_api(setup_user, monkeypatch):
#     user = setup_user

#     # Add API to the user
#     user.add_api('OpenAI_agent', '')
#     user.add_api('Qwen', '')
#     # Check if the API is added correctly
#     api_dict = user.get_api_dict()
#     assert 'OpenAI_agent' in api_dict
#     assert api_dict['OpenAI_agent'] == ''

#     # Check if the available models are updated correctly
#     available_models = user.get_available_models()
#     assert 'OpenAI_agent' in available_models
    # assert available_models['OpenAI_agent'] == ['model1', 'model2']

# def test_del_api(setup_user, monkeypatch):
#     user = setup_user

#     # Mock the external API class
#     class MockApi:
#         def __init__(self, api_key):
#             self.api_key = api_key
#             self.supported_models = ['model1', 'model2']

#     monkeypatch.setattr('data.user.service_provider_name_Api', MockApi)

#     # Add API to the user
#     user.add_api('service_provider_name', 'api_key_123')

#     # Delete the API from the user
#     user.del_api('service_provider_name')

#     # Check if the API is deleted correctly
#     api_dict = user.get_api_dict()
#     assert 'service_provider_name' not in api_dict

#     # Check if the available models are updated correctly
#     available_models = user.get_available_models()
#     assert 'service_provider_name' not in available_models

# def test_get_chat(setup_user):
#     user = setup_user

#     # Create a chat instance
#     chat = Chat(cid='chat001', title='Test Chat')

#     # Add the chat to the user
#     user.add_chat(chat)

#     # Retrieve the chat from the user
#     retrieved_chat = user.get_chat('chat001')

#     # Check if the chat is retrieved correctly
#     assert retrieved_chat['chat_id'] == 'chat001'
#     assert retrieved_chat['chat_title'] == 'Test Chat'

# def test_get_api(setup_user, monkeypatch):
#     user = setup_user

#     # Mock the external API class
#     class MockApi:
#         def __init__(self, api_key):
#             self.api_key = api_key
#             self.supported_models = ['model1', 'model2']

#     monkeypatch.setattr('data.user.service_provider_name_Api', MockApi)

#     # Add API to the user
#     user.add_api('service_provider_name', 'api_key_123')

#     # Retrieve the API from the user
#     api_key = user.get_api('service_provider_name')

#     # Check if the API is retrieved correctly
#     assert api_key == 'api_key_123'


user = User(username='user001', password='password123')

# Create a chat instance
chat = Chat(cid='chat001', title='Test Chat', msg_list=[Message(role='user', name='Alice', msg='Hello!', code='001')._to_db_dict(), Message(role='bot', name='Bot1', msg='Hi there!', code='002')._to_db_dict()], recv_msg_tmp={'BotModel1': Message(role='bot', name='Bot1', msg='Hi there!', code='002')._to_db_dict()})

# Add the chat to the user
user.add_chat(chat)

# Check if the chat is added correctly
chat_dict = user.get_chat_dict()
print(chat_dict)
assert 'chat001' in chat_dict
added_chat = chat_dict['chat001']
assert added_chat['chat_id'] == 'chat001'
assert added_chat['chat_title'] == 'Test Chat'