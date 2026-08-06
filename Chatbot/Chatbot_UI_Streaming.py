import streamlit as st
from Chatbot_Backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import uuid, json

# *************** Utility Functions ****************
def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def restore_thread(thread_id):
    return chatbot.get_state(config={'configurable':{'thread_id': thread_id}}).values['messages']

#*********** Session Setup *****************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])

# ****************** Sidebar UI *********************************
st.sidebar.title('LangGraph Chatbot')
if st.sidebar.button('New Chat'):
    reset_chat()
st.sidebar.header('My Conversations')
for thread in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread)):
        st.session_state['thread_id'] = thread
        messages = restore_thread(thread)

        temp_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = 'user'
            else:
                role='ai'
            temp_messages.append({'role': role, 'content': message.content})
        st.session_state['message_history'] = temp_messages





# ****************** Main UI *************************************

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

chat_input = st.chat_input('Type Here')

if chat_input:
    st.session_state['message_history'].append({'role':'user', 'content': chat_input})
    with st.chat_message('user'):
        st.text(chat_input)

    CONFIG = {"configurable":{"thread_id":st.session_state['thread_id']}}

    with st.chat_message('ai'):
        status_holder = {"box":None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=chat_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name","tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"Using '{tool_name}'....",
                            expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label="Using '{tool_name}'....",
                            state="running",
                            expanded=True
                        )
                    image = json.loads(message_chunk.content)
                    yield st.image(image["url"])
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content 
        
        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="Tool finished",
                state="complete",
                expanded=True
            )
    st.session_state['message_history'].append({'role':'ai','content':ai_message})