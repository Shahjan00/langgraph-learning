import streamlit as st
from backend import chatbot, get_all_thread
from langchain.messages import HumanMessage
import uuid


#=========================== Util Functions ===============================

def generate_thread_id():
    return str(uuid.uuid4())          # str, so it matches DB thread ids

def reset_chat():
    st.session_state['thread_id'] = generate_thread_id()
    st.session_state['message_history'] = []
    # no add_threads() here, it's added on first message

def add_threads(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    CONFIG = {'configurable': {'thread_id': thread_id}}
    return chatbot.get_state(config=CONFIG).values.get('messages', [])   # safe


#=========================== SESSION SETUP ===============================

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = get_all_thread()

# removed: add_threads(st.session_state['thread_id'])


#=========================== Side Bar ===============================

st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat", width="stretch"):
    reset_chat()

st.sidebar.header("My Conversation")

for thread_id in st.session_state['chat_threads']:
    if st.sidebar.button(str(thread_id[:20]), key=f"thread_{thread_id}", width="stretch"):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.text})

        st.session_state['message_history'] = temp_messages


#=========================== Main Ui ===============================

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        if message['role'] == 'assistant':
            st.markdown(message['content'])
        else:
            st.text(message['content'])

user_input = st.chat_input('Type Here')

if user_input:
    is_new_thread = st.session_state['thread_id'] not in st.session_state['chat_threads']
    add_threads(st.session_state['thread_id'])   # registered only now

    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.text for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['message_history'].append({"role": "assistant", "content": ai_message})

    if is_new_thread:
        st.rerun()