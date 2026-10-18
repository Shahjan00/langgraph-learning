import streamlit as st
from backend import chatbot, get_all_thread
from langchain.messages import HumanMessage, AIMessage, ToolMessage
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
            if isinstance(msg, HumanMessage):
                temp_messages.append({'role': 'user', 'content': msg.text, 'tools': []})
            elif isinstance(msg, AIMessage):
                # start a new assistant bubble only if the last one isn't already assistant
                if not temp_messages or temp_messages[-1]['role'] != 'assistant':
                    temp_messages.append({'role': 'assistant', 'content': '', 'tools': []})

                for tc in msg.tool_calls:                        # empty AI msg -> just grab tool name
                    temp_messages[-1]['tools'].append(tc['name'])

                temp_messages[-1]['content'] += msg.text 

        st.session_state['message_history'] = temp_messages


#=========================== Main Ui ===============================

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        for t in message.get('tools', []):
            st.status(f"Using `{t}`", state="complete", expanded=False)
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

    tools_used = []

    with st.chat_message('assistant'):
        status_holder = {"box" : None}
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    tools_used.append(tool_name)

                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"Using `{tool_name}`...", expanded=True
                        )
                    else:
                        status_holder['box'].update(
                            label=f"Using `{tool_name}`...",
                            state="running",
                            expanded=True
                        )

                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.text

        ai_message = st.write_stream(ai_only_stream())

        if status_holder['box'] is not None:
            status_holder["box"].update(state="complete", expanded=False)

    st.session_state['message_history'].append({"role": "assistant", "content": ai_message,"tools": tools_used})

    if is_new_thread:
        st.rerun()