import pytest
import data

@pytest.fixture
def setup_chat():
    # Create a new chat instance
    chat = data.Chat(cid='chat001', title='Test Chat')
    return chat

def test_chat_initialization(setup_chat):
    chat = setup_chat
    assert chat.get_chat_id() == 'chat001'
    assert chat.get_chat_title() == 'Test Chat'
    assert chat.get_msg_list() == []
    assert chat.get_recv_msg_tmp() == {}

# def test_add_message(setup_chat):
#     chat = setup_chat

#     # Create a message instance
#     msg = data.Message(role='user', name='Alice', msg='Hello!', code='001')

#     # Add the message to the chat
#     chat.add_msg(msg)

#     # Check if the message is added correctly
#     assert len(chat.get_msg_list()) == 1
#     assert chat.get_msg_list()[0].msg == 'Hello!'
#     assert chat.get_msg_list()[0].role== 'user'
#     assert chat.get_msg_list()[0].name == 'Alice'
#     assert chat.get_msg_list()[0].code == '001'

# def test_add_and_retrieve_received_message(setup_chat):
#     chat = setup_chat

#     # Create a received message instance
#     recv_msg = data.Message(role='bot', name='Bot1', msg='Hi there!', code='002')

#     # Add the received message to the chat
#     chat.add_recv_msg('BotModel1', recv_msg)

#     # Retrieve the received message
#     retrieved_msg = chat.get_recv_msg_tmp()['BotModel1']

#     # Check if the received message is retrieved correctly
#     assert retrieved_msg.msg == 'Hi there!'
#     assert retrieved_msg.role == 'bot'
#     assert retrieved_msg.name == 'Bot1'
#     assert retrieved_msg.code == '002'

# def test_set_title(setup_chat):
#     chat = setup_chat

#     # Set a new title
#     chat.set_title('New Title')

#     # Check if the title is updated correctly
#     assert chat.get_chat_title() == 'New Title'

def test_sel_recv_msg(setup_chat):
    chat = setup_chat

    # Create a received message instance
    recv_msg = data.Message(role='bot', name='Bot1', msg='Hi again!', code='003')

    # Add the received message to the chat
    chat.add_recv_msg('BotModel2', recv_msg)
    print(chat.get_recv_msg_tmp())

    # Select the received message and add it to the message list
    chat.sel_recv_msg('BotModel2')
    print(chat.get_recv_msg_tmp())
    exit()
    # Check if the message list is updated correctly
    msg_list = chat.get_msg_list()
    assert len(msg_list) == 1
    assert msg_list[0].msg == 'Hi again!'
    assert msg_list[0].role == 'bot'
    assert msg_list[0].name == 'Bot1'
    assert msg_list[0].code == '003'

    # Check if the received message temp storage is cleared
    assert chat.get_recv_msg_tmp() == {}

