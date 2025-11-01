import streamlit as st
import pandas as pd
import os
import hashlib
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama

# ---------------------------
# User Authentication
# ---------------------------
USER_FILE = "users.txt"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password):
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            pass
    with open(USER_FILE, "r") as f:
        users = [line.strip().split(",")[0] for line in f.readlines()]
    if username in users:
        return False, "Username already exists."
    with open(USER_FILE, "a") as f:
        f.write(f"{username},{hash_password(password)}\n")
    return True, "Signup successful! Please login."

def login_user(username, password):
    if not os.path.exists(USER_FILE):
        return False
    hashed = hash_password(password)
    with open(USER_FILE, "r") as f:
        for line in f.readlines():
            user, pwd = line.strip().split(",")
            if user == username and pwd == hashed:
                return True
    return False

# ---------------------------
# Initialize session_state
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "login"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "messages" not in st.session_state:
    st.session_state.messages = {}  # key: username, value: list of chat messages

# ---------------------------
# Page Navigation
# ---------------------------
def show_login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user(username, password):
            st.session_state.logged_in = True
            st.session_state.current_user = username
            if username not in st.session_state.messages:
                st.session_state.messages[username] = []
            st.session_state.page = "app"
            st.stop()
        else:
            st.error("Invalid username or password")

    st.write("Don't have an account?")
    if st.button("Go to Signup"):
        st.session_state.page = "signup"
        st.stop()

def show_signup():
    st.title("📝 Signup")
    username = st.text_input("Choose Username")
    password = st.text_input("Choose Password", type="password")

    if st.button("Signup"):
        success, msg = signup_user(username, password)
        if success:
            st.success(msg)
            st.session_state.page = "login"
            st.stop()
        else:
            st.error(msg)

    st.write("Already have an account?")
    if st.button("Go to Login"):
        st.session_state.page = "login"
        st.stop()
# ---------------------------
# Navbar with Logout
# ---------------------------
def navbar():
    st.markdown(
        """
        <style>
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #333;
            padding: 10px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .navbar-title {
            font-size: 20px;
            font-weight: bold;
            color: white;
        }
        .navbar-links {
            display: flex;
            gap: 15px;
        }
        .navbar-links button {
            background: #feb236;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Layout: Title on left, buttons on right
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<div class='navbar'><span class='navbar-title'>💊 AI Prescription Guidance</span></div>", unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.page = "login"
            st.session_state.messages = {}  # optional: clear all chats
            st.stop()

# ---------------------------
# AI Prescription Guidance App
# ---------------------------
def show_app():
    navbar() 
    st.title(f"💊 AI Prescription Guidance - {st.session_state.current_user}")
    st.write("Ask about medicine availability, alternatives, dosage, or use cases.")

    # -----------------------
    # Load Medicine CSV
    # -----------------------
    df = pd.read_csv("medicines.csv")

    # -----------------------
    # Prepare Documents for Vector Store
    # -----------------------
    documents = [
        f"{row['Medicine_Name']} {row['Strength']} is used for {row['Use_Case']}. "
        f"Alternative: {row['Alternative']}. Stock: {row['Stock']}. Dosage: {row['Dosage_Instruction']}"
        for _, row in df.iterrows()
    ]

    # -----------------------
    # Initialize embeddings & vectorstore
    # -----------------------
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    VECTORSTORE_DIR = "vectorstore/"
    if not os.path.exists(VECTORSTORE_DIR):
        vectorstore = Chroma.from_texts(documents, embeddings, persist_directory=VECTORSTORE_DIR)
        vectorstore.persist()
    else:
        vectorstore = Chroma(persist_directory=VECTORSTORE_DIR, embedding_function=embeddings)

    # -----------------------
    # Initialize LLM and RAG Agent
    # -----------------------
    llm = Ollama(model="gemma:2b")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

    # -----------------------
    # Medicine lookup
    # -----------------------
    def get_med_info(query, df):
        query_lower = query.lower()
        for _, row in df.iterrows():
            medicine_name = row['Medicine_Name'].lower()
            use_case_words = [w.strip() for w in row['Use_Case'].lower().split(',')]
            if medicine_name in query_lower or any(word in query_lower for word in use_case_words):
                stock_value = row['Stock'].strip().lower()
                stock_msg = "available" if stock_value in ["yes", "available", "in stock"] else "out of stock"
                alternative = row['Alternative'] if stock_msg != "available" else None
                dosage = row['Dosage_Instruction']
                if "available" in query_lower or "stock" in query_lower:
                    return f"{row['Medicine_Name']} is {stock_msg}." + (f" Alternative: {alternative}." if alternative else "")
                elif "dosage" in query_lower or "take" in query_lower or "how" in query_lower:
                    return f"Dosage for {row['Medicine_Name']}: {dosage}."
                elif "alternative" in query_lower or "substitute" in query_lower:
                    return f"Alternative for {row['Medicine_Name']}: {alternative if alternative else 'No alternative needed, medicine is available.'}"
                else:
                    return (
                        f"{row['Medicine_Name']} {row['Strength']} is used for {row['Use_Case']}. "
                        f"Stock: {stock_msg}. " +
                        (f"Alternative: {alternative}. " if alternative else "") +
                        f"Dosage: {dosage}. Please consult a doctor before use."
                    )
        return None

    # -----------------------
    # Format response
    # -----------------------
    def format_response_pointwise(text):
        points = text.split('. ')
        formatted = ""
        for point in points:
            if point.strip():
                formatted += f"• {point.strip()}\n"
        return formatted

    # -----------------------
    # UI
    # -----------------------
    st.markdown(
        """
        <style>
        body {
            background: linear-gradient(135deg, #6B5B95, #feb236, #d64161);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            color: white;
        }
        @keyframes gradientBG {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        .user-msg {
            background: #28a745;
            padding: 10px 15px;
            border-radius: 15px;
            text-align: right;
            margin: 5px 0;
            color: white;
        }
        .bot-msg {
            background: #feb236;
            padding: 10px 15px;
            border-radius: 15px;
            text-align: left;
            margin: 5px 0;
            color: #000;
        }
        .scrollable {
            max-height: 400px;
            overflow-y: auto;
        }
        </style>
        """, unsafe_allow_html=True
    )

    query = st.text_input("Type your query here...", placeholder="Ask about medicine...")

    if query:
        st.session_state.messages[st.session_state.current_user].append({"from": "user", "text": query})
        with st.spinner("Generating response..."):
            med_response = get_med_info(query, df)
            if med_response:
                response_text = format_response_pointwise(med_response)
            else:
                try:
                    response = qa.invoke(query)
                    rag_response = response.get('result', 'No RAG response available.')
                except Exception as e:
                    rag_response = f"Error generating RAG response: {str(e)}"
                response_text = format_response_pointwise(rag_response)
            st.session_state.messages[st.session_state.current_user].append({"from": "bot", "text": response_text})

    # Display chat messages
    st.markdown('<div class="chat-box scrollable">', unsafe_allow_html=True)
    for msg in st.session_state.messages.get(st.session_state.current_user, []):
        cls = "user-msg" if msg["from"] == "user" else "bot-msg"
        st.markdown(f"<div class='{cls}'>{msg['text'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Show page based on session_state
# ---------------------------
if st.session_state.page == "login":
    show_login()
elif st.session_state.page == "signup":
    show_signup()
elif st.session_state.page == "app":
    show_app()
