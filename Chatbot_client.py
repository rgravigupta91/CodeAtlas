import streamlit as st
import requests
import uuid
import json

SERVER_URL = "http://localhost:8000"
st.set_page_config(page_title="CodeAtlas", page_icon="🗺️")

# ─── API Helpers ─────────────────────────────────────────────────────────────

def fetch_threads():
    try:
        return requests.get(f"{SERVER_URL}/threads").json()
    except Exception:
        return []

def fetch_history(thread_id: str):
    try:
        return requests.get(f"{SERVER_URL}/threads/{thread_id}/history").json()
    except Exception:
        return []

def rename_thread_api(thread_id: str, name: str):
    try:
        requests.put(f"{SERVER_URL}/threads/{thread_id}/name", json={"name": name})
    except Exception:
        pass

def delete_thread_api(thread_id: str):
    try:
        requests.delete(f"{SERVER_URL}/threads/{thread_id}")
    except Exception:
        pass

def token_stream(thread_id: str, message: str):
    with requests.post(
        f"{SERVER_URL}/chat",
        json={"thread_id": thread_id, "message": message},
        stream=True,
    ) as response:
        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                data = json.loads(line[6:])
                yield data

# ─── Utility ─────────────────────────────────────────────────────────────────

def generate_thread_id() -> str:
    return str(uuid.uuid4())

def reset_chat():
    st.session_state["thread_id"] = generate_thread_id()
    st.session_state["message_history"] = []
    st.session_state["editing_thread"] = None
    st.session_state["deleting_thread"] = None

def find_thread(thread_id: str):
    return next(
        (t for t in st.session_state["chat_threads"] if t["thread_id"] == thread_id),
        None,
    )

def add_thread_locally(thread_id: str, name: str):
    if not find_thread(thread_id):
        st.session_state["chat_threads"].insert(0, {"thread_id": thread_id, "name": name})

def update_thread_name_locally(thread_id: str, name: str):
    thread = find_thread(thread_id)
    if thread:
        thread["name"] = name

# ─── Session Setup ────────────────────────────────────────────────────────────

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = fetch_threads()

if "editing_thread" not in st.session_state:
    st.session_state["editing_thread"] = None

if "deleting_thread" not in st.session_state:
    st.session_state["deleting_thread"] = None

if "naming_new_thread" not in st.session_state:
    st.session_state["naming_new_thread"] = False

# ─── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.title("CodeAtlas")

if st.sidebar.button("➕ New Chat"):
    st.session_state["naming_new_thread"] = True
    st.session_state["editing_thread"] = None
    st.session_state["deleting_thread"] = None

# Name dialog shown immediately after clicking New Chat
if st.session_state["naming_new_thread"]:
    new_name = st.sidebar.text_input(
        "Thread name",
        placeholder="e.g. Payment Flow",
        key="new_thread_name_input",
    )
    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.sidebar.button("Start", type="primary", key="start_new_thread"):
            name = new_name.strip()
            if name:
                thread_id = generate_thread_id()
                st.session_state["thread_id"] = thread_id
                st.session_state["message_history"] = []
                st.session_state["editing_thread"] = None
                st.session_state["deleting_thread"] = None
                st.session_state["naming_new_thread"] = False
                rename_thread_api(thread_id, name)
                add_thread_locally(thread_id, name)
                st.rerun()
    with c2:
        if st.sidebar.button("Cancel", key="cancel_new_thread"):
            st.session_state["naming_new_thread"] = False
            st.rerun()

st.sidebar.header("My Conversations")

for thread in st.session_state["chat_threads"]:
    thread_id = thread["thread_id"]
    display_name = thread["name"]

    col1, col2, col3 = st.sidebar.columns([4, 1, 1])
    with col1:
        if st.button(display_name, key=f"thread_{thread_id}", use_container_width=True):
            st.session_state["thread_id"] = thread_id
            st.session_state["editing_thread"] = None
            st.session_state["deleting_thread"] = None
            st.session_state["naming_new_thread"] = False
            st.session_state["message_history"] = fetch_history(thread_id)
    with col2:
        if st.button("✏️", key=f"edit_{thread_id}"):
            st.session_state["editing_thread"] = thread_id
            st.session_state["deleting_thread"] = None
    with col3:
        if st.button("🗑️", key=f"delete_{thread_id}"):
            st.session_state["deleting_thread"] = thread_id
            st.session_state["editing_thread"] = None

    if st.session_state["editing_thread"] == thread_id:
        new_name = st.sidebar.text_input("Rename", value=display_name, key=f"rename_{thread_id}")
        if st.sidebar.button("Save", key=f"save_{thread_id}"):
            clean_name = new_name.strip() or display_name
            rename_thread_api(thread_id, clean_name)
            update_thread_name_locally(thread_id, clean_name)
            st.session_state["editing_thread"] = None
            st.rerun()

    if st.session_state["deleting_thread"] == thread_id:
        st.sidebar.warning(f"Delete **{display_name}**?")
        dcol1, dcol2 = st.sidebar.columns(2)
        with dcol1:
            if st.button("Yes, delete", key=f"confirm_delete_{thread_id}", type="primary"):
                delete_thread_api(thread_id)
                st.session_state["chat_threads"] = [
                    t for t in st.session_state["chat_threads"] if t["thread_id"] != thread_id
                ]
                if st.session_state["thread_id"] == thread_id:
                    reset_chat()
                st.session_state["deleting_thread"] = None
                st.rerun()
        with dcol2:
            if st.button("Cancel", key=f"cancel_delete_{thread_id}"):
                st.session_state["deleting_thread"] = None
                st.rerun()

# ─── Main Chat UI ─────────────────────────────────────────────────────────────

for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

chat_input = st.chat_input("Type Here")

if chat_input:
    is_new_thread = not find_thread(st.session_state["thread_id"])
    if is_new_thread:
        auto_name = chat_input[:40] + ("..." if len(chat_input) > 40 else "")
        rename_thread_api(st.session_state["thread_id"], auto_name)
        add_thread_locally(st.session_state["thread_id"], auto_name)

    st.session_state["message_history"].append({"role": "user", "content": chat_input})
    with st.chat_message("user"):
        st.markdown(chat_input)

    with st.chat_message("ai"):
        status_holder = {"box": None}
        ai_text = ""
        response_placeholder = st.empty()

        for event in token_stream(st.session_state["thread_id"], chat_input):
            if event["type"] == "token":
                ai_text += event["content"]
                response_placeholder.markdown(ai_text)

            elif event["type"] == "tool":
                tool_name = event["name"]
                if status_holder["box"] is None:
                    status_holder["box"] = st.status(f"Using '{tool_name}'...", expanded=True)
                try:
                    image_data = json.loads(event["content"])
                    if "url" in image_data:
                        st.image(image_data["url"])
                except Exception:
                    pass

            elif event["type"] == "done":
                break

        if status_holder["box"] is not None:
            status_holder["box"].update(label="Tool finished", state="complete", expanded=True)

    st.session_state["message_history"].append({"role": "ai", "content": ai_text})

    # Rerun after first message so the sidebar reflects the new thread immediately
    if is_new_thread:
        st.rerun()
