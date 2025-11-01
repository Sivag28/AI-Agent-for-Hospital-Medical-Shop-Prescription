import streamlit as st
import hashlib
import os

USER_FILE = "users.txt"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
def login_user(username, password):
    if not os.path.exists(USER_FILE):
        return False
    hashed = hash_password(password)
    with open(USER_FILE, "r") as f:
        for line in f.readlines():
            parts = line.strip().split(",")
            if len(parts) != 2:  # skip bad lines
                continue
            user, pwd = parts
            if user == username and pwd == hashed:
                return True
    return False


st.set_page_config(page_title="Login", page_icon="🔐")

st.title("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if login_user(username, password):
        st.session_state.logged_in = True
        st.session_state.current_user = username
        if "messages" not in st.session_state:
            st.session_state.messages = {}
        if username not in st.session_state.messages:
            st.session_state.messages[username] = []
        st.success(f"Welcome back, {username}!")
        st.button("Go to AI Prescription Guidance App", on_click=lambda: st.session_state.update({"page": "app"}))
    else:
        st.error("Invalid username or password")

st.write("Don't have an account? Go to Signup page.")
if st.button("Go to Signup Page"):
    st.session_state.update({"page": "signup"})
