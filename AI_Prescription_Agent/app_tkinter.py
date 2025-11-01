import tkinter as tk
from tkinter import messagebox, scrolledtext
import pandas as pd
import os
import hashlib
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama

# --------------------------- Constants ---------------------------
USER_FILE = "users.txt"
MEDICINES_CSV = "medicines.csv"
VECTORSTORE_DIR = "vectorstore/"

# --------------------------- User Authentication Functions ---------------------------
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

# --------------------------- Medicine and AI Functions ---------------------------
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

def format_response_pointwise(text):
    points = text.split('. ')
    formatted = ""
    for point in points:
        if point.strip():
            formatted += f"• {point.strip()}\n"
    return formatted

# --------------------------- Tkinter App Class ---------------------------
class TkinterApp(tk.Tk):
    def __init__(self):
        print("Starting TkinterApp __init__")
        super().__init__()
        self.title("AI Prescription Guidance")
        self.geometry("1000x700")
        self.configure(bg="#f0f0f0")
        # Center the main window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1000x700+{x}+{y}")

        # Session state
        self.logged_in = False
        self.current_user = None
        self.messages = {}

        # Load medicine data
        print("Loading medicine data")
        self.df = pd.read_csv(MEDICINES_CSV)

        # Initialize AI components later to reduce loading time
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.qa = None

        # Main app frame initially not placed
        self.main_frame = MainAppFrame(self)

        # Login and Signup popups (Toplevel windows)
        self.login_popup = None
        self.signup_popup = None
        self.loading_popup = None

        # Show login popup initially
        print("Showing login popup")
        self.show_login_popup()

    def show_login_popup(self):
        if self.login_popup is None or not self.login_popup.winfo_exists():
            self.login_popup = LoginPopup(self)
        self.login_popup.deiconify()
        self.login_popup.lift()
        self.login_popup.focus_force()
        # Hide main frame if placed
        try:
            self.main_frame.place_forget()
        except:
            pass

    def show_signup_popup(self):
        if self.signup_popup is None or not self.signup_popup.winfo_exists():
            self.signup_popup = SignupPopup(self)
        self.signup_popup.deiconify()
        self.signup_popup.lift()
        self.signup_popup.focus_force()
        # Hide main frame if placed
        try:
            self.main_frame.place_forget()
        except:
            pass

    def close_login_popup(self):
        print("close_login_popup called")
        if self.login_popup and self.login_popup.winfo_exists():
            self.login_popup.destroy()
            self.login_popup = None

        # Show loading popup
        self.loading_popup = LoadingPopup(self)
        self.loading_popup.deiconify()
        self.loading_popup.lift()
        self.loading_popup.focus_force()
        self.update()  # Force update to show popup

        # Initialize AI components after login to reduce loading time
        if self.embeddings is None:
            print("Initializing AI components")
            # Temporarily comment out AI initialization to test GUI startup
            """
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"}
            )
            if not os.path.exists(VECTORSTORE_DIR):
                documents = [
                    f"{row['Medicine_Name']} {row['Strength']} is used for {row['Use_Case']}. "
                    f"Alternative: {row['Alternative']}. Stock: {row['Stock']}. Dosage: {row['Dosage_Instruction']}"
                    for _, row in self.df.iterrows()
                ]
                self.vectorstore = Chroma.from_texts(documents, self.embeddings, persist_directory=VECTORSTORE_DIR)
                self.vectorstore.persist()
            else:
                self.vectorstore = Chroma(persist_directory=VECTORSTORE_DIR, embedding_function=self.embeddings)

            self.llm = Ollama(model="gemma:2b")
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            self.qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff",
                                                  retriever=self.retriever, return_source_documents=True)
            """

        # Destroy loading popup
        if self.loading_popup and self.loading_popup.winfo_exists():
            self.loading_popup.destroy()
            self.loading_popup = None

        # Show main frame
        self.main_frame.place(relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center")
        self.main_frame.lift()

    def close_signup_popup(self):
        if self.signup_popup and self.signup_popup.winfo_exists():
            self.signup_popup.destroy()
            self.signup_popup = None
        # Show main frame
        self.main_frame.place(relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center")
        self.main_frame.lift()

# --------------------------- Login Popup ---------------------------
class LoginPopup(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Login")
        self.configure(bg="white")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(master)  # Make it modal
        self.grab_set()  # Grab focus
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")

        tk.Label(self, text="🔐 Login", font=("Arial", 24, "bold"), bg="white").pack(pady=20)
        tk.Label(self, text="Username:", bg="white").pack()
        self.username_entry = tk.Entry(self, bg="yellow")
        self.username_entry.pack()
        tk.Label(self, text="Password:", bg="white").pack()
        self.password_entry = tk.Entry(self, show="*", bg="yellow")
        self.password_entry.pack()
        tk.Button(self, text="Login", command=self.login,
                  bg="#4CAF50", fg="white", activebackground="#45a049").pack(pady=10)
        tk.Label(self, text="Don't have an account?", bg="white").pack()
        tk.Button(self, text="Go to Signup", command=self.go_to_signup,
                  bg="#2196F3", fg="white", activebackground="#1e88e5").pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if login_user(username, password):
            self.master.logged_in = True
            self.master.current_user = username
            if username not in self.master.messages:
                self.master.messages[username] = []
            self.master.close_login_popup()
            self.master.main_frame.update_title()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def go_to_signup(self):
        self.master.close_login_popup()
        self.master.show_signup_popup()

# --------------------------- Loading Popup ---------------------------
class LoadingPopup(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Loading")
        self.configure(bg="lightgreen")
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.winfo_screenheight() // 2) - (150 // 2)
        self.geometry(f"300x150+{x}+{y}")

        tk.Label(self, text="🔄 Loading AI Components...", font=("Arial", 14), bg="green").pack(pady=30)
        tk.Label(self, text="Please wait...", bg="white").pack()

# --------------------------- Signup Popup ---------------------------
class SignupPopup(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Signup")
        self.configure(bg="white")
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(master)  # Make it modal
        self.grab_set()  # Grab focus
        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (350 // 2)
        self.geometry(f"400x350+{x}+{y}")

        tk.Label(self, text="📝 Signup", font=("Arial", 24, "bold"), bg="white").pack(pady=20)
        tk.Label(self, text="Choose Username:", bg="white").pack()
        self.username_entry = tk.Entry(self, bg="yellow")
        self.username_entry.pack()
        tk.Label(self, text="Choose Password:", bg="white").pack()
        self.password_entry = tk.Entry(self, show="*", bg="yellow")
        self.password_entry.pack()
        tk.Button(self, text="Signup", command=self.signup,
                  bg="#4CAF50", fg="white", activebackground="#45a049").pack(pady=10)
        tk.Label(self, text="Already have an account?", bg="white").pack()
        tk.Button(self, text="Go to Login", command=self.go_to_login,
                  bg="#2196F3", fg="white", activebackground="#1e88e5").pack()

    def signup(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        success, msg = signup_user(username, password)
        if success:
            messagebox.showinfo("Success", msg)
            self.master.close_signup_popup()
            self.master.show_login_popup()
        else:
            messagebox.showerror("Error", msg)

    def go_to_login(self):
        self.master.close_signup_popup()
        self.master.show_login_popup()



# --------------------------- Main App Frame ---------------------------
class MainAppFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="lightblue", bd=2, relief="solid")
        self.master = master
        self.configure(width=800, height=600)

        # Navbar
        navbar_frame = tk.Frame(self, bg="#333", height=50)
        navbar_frame.pack(fill="x")
        tk.Label(navbar_frame, text="💊 AI Prescription Guidance", bg="#333", fg="white",
                 font=("Arial", 16, "bold")).pack(side="left", padx=20)
        tk.Button(navbar_frame, text="🚪 Logout", command=self.logout,
                  bg="#f44336", fg="white", activebackground="#e53935").pack(side="right", padx=20)

        # Title
        self.title_label = tk.Label(self, text="", font=("Arial", 18), bg="lightblue")
        self.title_label.pack(pady=10)

        tk.Label(self, text="Ask about medicine availability, alternatives, dosage, or use cases.",
                 bg="lightblue").pack()

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=15, bg="lightyellow")
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Input frame
        input_frame = tk.Frame(self, bg="lightblue")
        input_frame.pack(fill="x", padx=10, pady=10)
        # Changed from Entry to Text widget to allow height adjustment
        self.query_entry = tk.Text(input_frame, height=3, bg="yellow")
        self.query_entry.pack(side="left", fill="x", expand=True)
        tk.Button(input_frame, text="Send", command=self.send_query,
                  bg="#4CAF50", fg="white", activebackground="#45a049").pack(side="right")

        self.update_title()

    def update_title(self):
        if self.master.current_user:
            self.title_label.config(text=f"💊 AI Prescription Guidance - {self.master.current_user}")

    def logout(self):
        self.master.logged_in = False
        self.master.current_user = None
        self.master.messages = {}
        self.chat_display.delete(1.0, tk.END)
        # Hide main frame
        self.master.main_frame.place_forget()
        self.master.show_login_popup()

    def send_query(self):
        query = self.query_entry.get("1.0", tk.END).strip()
        if not query:
            return
        self.query_entry.delete("1.0", tk.END)

        # Add user message
        self.master.messages[self.master.current_user].append({"from": "user", "text": query})
        self.display_message("user", query)

        # Generate response
        med_response = get_med_info(query, self.master.df)
        if med_response:
            response_text = format_response_pointwise(med_response)
        else:
            try:
                response = self.master.qa.invoke(query)
                rag_response = response.get('result', 'No RAG response available.')
            except Exception as e:
                rag_response = f"Error generating RAG response: {str(e)}"
            response_text = format_response_pointwise(rag_response)

        # Add bot message
        self.master.messages[self.master.current_user].append({"from": "bot", "text": response_text})
        self.display_message("bot", response_text)

    def display_message(self, sender, text):
        tag = "user" if sender == "user" else "bot"
        self.chat_display.insert(tk.END, f"{sender.capitalize()}: {text}\n\n", tag)
        self.chat_display.see(tk.END)

# --------------------------- Run the App ---------------------------
if __name__ == "__main__":
    app = TkinterApp()
    app.mainloop()
