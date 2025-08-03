import streamlit as st
import io
import PyPDF2
import docx
from groq import Groq
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Bajaj Finserv Policy Assistant",
    page_icon="https://www.bajajfinserv.in/assets_bajaj_finserv/images/favicon/favicon-32x32.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- IMPORTANT: PASTE YOUR GROQ API KEY HERE ---
GROQ_API_KEY = "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"

# --- State Management ---
if 'uploaded_policies' not in st.session_state:
    st.session_state.uploaded_policies = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- Custom CSS for a Branded, Beautiful UI ---
st.markdown("""
<style>
    /* Keyframes for fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Base styling with a professional dark blue background */
    .stApp {
        background-color: #0d1117; /* A professional dark background */
        color: #e0e0e0;
    }

    /* Main title with a clean, bright look */
    .main-title {
        color: #ffffff;
        text-align: center;
        padding-bottom: 20px;
        font-size: 2.8em;
        font-weight: 700;
    }
    
    /* Subheader styling using Bajaj Finserv Blue */
    h3 {
        color: #0078ff; 
        border-bottom: 1px solid #0078ff;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }

    /* Glassmorphism container with fade-in animation */
    .glass-container {
        background: rgba(26, 35, 58, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(0, 120, 255, 0.2);
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    /* Styling for Streamlit buttons with Bajaj Finserv Blue */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #0078ff;
        color: #ffffff;
        background-color: #0078ff;
        transition: all 0.3s ease-in-out;
        transform: scale(1);
    }
    .stButton>button:hover {
        background-color: #0056b3;
        border-color: #0056b3;
        box-shadow: 0 0 15px rgba(0, 120, 255, 0.5);
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)


# --- Helper Functions (No changes needed) ---

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        st.error(f"Error reading DOCX file: {e}")
        return None

def extract_text_from_txt(file):
    try:
        return file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading TXT file: {e}")
        return None

def split_text_into_chunks(text, chunk_size=400, overlap=50):
    words = re.split(r'(\s+)', text)
    chunks = []
    current_chunk_words = []
    word_count = 0
    for i, word in enumerate(words):
        current_chunk_words.append(word)
        if not word.isspace():
            word_count += 1
        if word_count >= chunk_size:
            chunks.append("".join(current_chunk_words))
            overlap_words = current_chunk_words[-overlap*2:]
            current_chunk_words = overlap_words
            word_count = overlap
    if current_chunk_words:
        chunks.append("".join(current_chunk_words))
    return chunks

def find_relevant_chunks(query, chunks, top_k=7):
    query_words = set(re.findall(r'\w+', query.lower()))
    if not query_words:
        return chunks[:top_k]
    scored_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_words = set(re.findall(r'\w+', chunk.lower()))
        score = len(query_words.intersection(chunk_words))
        if score > 0:
            scored_chunks.append((score, i, chunk))
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    relevant_chunks = [chunk for score, i, chunk in scored_chunks[:top_k]]
    if not relevant_chunks:
        return chunks[:2]
    return relevant_chunks


# --- Llama API Call ---

def build_prompt(question, context):
    return f"""
You are a very strict insurance claims adjudicator. Your primary task is to determine if a claim is covered based ONLY on the provided policy sections. You must adhere to all exclusions and waiting periods.

**RELEVANT POLICY DOCUMENT SECTIONS (CONTEXT):**
---
{context}
---

**USER'S QUERY:**
"{question}"

**YOUR TASK:**
1.  Analyze the user's query for key terms (e.g., condition, time since policy start, activity).
2.  **First, search the CONTEXT for any applicable EXCLUSIONS or WAITING PERIODS that match the user's query.** This is your most important step.
3.  If the query matches a specific exclusion (like hazardous sports) or fails to meet a waiting period (e.g., asking for cataract surgery after 6 months when the waiting period is 24 months), your answer **MUST** start with 'No,'.
4.  If you cannot find any specific exclusion or waiting period that applies, then check if the condition is generally covered. If it is, start your answer with 'Yes,'.
5.  After the 'Yes,' or 'No,', provide a clear explanation for your decision, quoting the specific clause or reason from the context.
"""

def call_llama_api(prompt):
    if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        st.error("Groq API Key not found. Please add your API key to the script.", icon="🚨")
        return None
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.1,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred while contacting the Groq API: {e}", icon="🔥")
        return None


# --- Streamlit App UI ---

st.markdown('<h1 class="main-title">Bajaj Finserv Policy Assistant</h1>', unsafe_allow_html=True)

# --- Sidebar for Upload and Chat History ---
with st.sidebar:
    st.header("Controls")
    
    with st.container(border=True):
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload PDFs, Word documents, or text files.",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.uploaded_policies:
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        file_extension = uploaded_file.name.split('.')[-1].lower()
                        text = None
                        if file_extension == "pdf":
                            text = extract_text_from_pdf(io.BytesIO(uploaded_file.getvalue()))
                        elif file_extension == "docx":
                            text = extract_text_from_docx(io.BytesIO(uploaded_file.getvalue()))
                        elif file_extension == "txt":
                            text = extract_text_from_txt(uploaded_file)
                        if text:
                            lines = text.split('\n')
                            extracted_title = next((line.strip() for line in lines if line.strip()), uploaded_file.name)
                            chunks = split_text_into_chunks(text)
                            st.session_state.uploaded_policies[uploaded_file.name] = {
                                "display_title": extracted_title,
                                "chunks": chunks
                            }
            st.success(f"{len(st.session_state.uploaded_policies)} documents ready.", icon="✅")

    st.header("Chat History")
    history_container = st.container(height=400, border=True)
    for message in st.session_state.chat_history:
        with history_container:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


# --- Main Interaction Area ---
st.header("Ask a Question")

if st.session_state.uploaded_policies:
    policy_titles = {key: data['display_title'] for key, data in st.session_state.uploaded_policies.items()}
    selected_key = st.selectbox(
        "Select a policy document to query",
        options=list(policy_titles.keys()),
        format_func=lambda key: policy_titles[key],
        index=None,
        placeholder="-- Choose from uploaded documents --"
    )
    user_query = st.text_area(
        "Enter your claim details",
        placeholder="e.g., Is my knee surgery covered if I have had the policy for 2 years?",
        key="user_query_input",
        height=150
    )
    if st.button("Process Claim", use_container_width=True):
        if not selected_key:
            st.warning("Please select a policy document first.", icon="⚠️")
        elif not user_query:
            st.warning("Please enter your claim details.", icon="⚠️")
        else:
            with st.spinner("Llama is analyzing the documents..."):
                all_chunks = st.session_state.uploaded_policies[selected_key]['chunks']
                relevant_chunks = find_relevant_chunks(user_query, all_chunks)
                focused_context = "\n\n...\n\n".join(relevant_chunks)
                full_prompt = build_prompt(user_query, focused_context)
                response_text = call_llama_api(full_prompt)
                
                # Add to chat history
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                if response_text:
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                else:
                    st.session_state.chat_history.append({"role": "assistant", "content": "Sorry, I encountered an error. Please try again."})
                
                # Rerun to update the history display immediately
                st.rerun()
else:
    st.info("Please upload a policy document in the sidebar to begin.")


# --- Display the latest response prominently ---
if st.session_state.chat_history:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.header("Latest Policy Analysis")
    latest_assistant_message = [msg for msg in reversed(st.session_state.chat_history) if msg["role"] == "assistant"]
    if latest_assistant_message:
        st.write(latest_assistant_message[0]["content"])
    st.markdown('</div>', unsafe_allow_html=True)
