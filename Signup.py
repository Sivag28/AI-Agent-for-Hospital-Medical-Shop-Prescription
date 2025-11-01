import streamlit as st
import hashlib
import os

USER_FILE = "users.txt"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password):
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            pass
    with open(USER_FILE, "r") as f:
        users = [line.strip().split(",")[0] for line in f.readlines() if "," in line]
    if username in users:
        return False, "Username already exists."
    with open(USER_FILE, "a") as f:
        f.write(f"{username},{hash_password(password)}\n")
    return True, "Signup successful! Please login."

st.set_page_config(page_title="Signup", page_icon="📝")

st.title("📝 Signup")

username = st.text_input("Choose a Username")
password = st.text_input("Choose a Password", type="password")

if st.button("Signup"):
    success, msg = signup_user(username, password)
    st.success(msg) if success else st.error(msg)
    if success:
        st.session_state.page = "login"
        st.stop()   # forces navigation

st.write("Already have an account?")
if st.button("Go to Login Page"):
    st.session_state.page = "login"
    st.stop()
