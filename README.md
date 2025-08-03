Bajaj Finserv Policy Assistant:
This project is a sophisticated, AI-powered web application designed to help users understand their insurance policies. Users can upload their policy documents in various formats (PDF, DOCX, TXT), and the application leverages a powerful Large Language Model (Llama 3 via the Groq API) to analyze the documents and answer user questions about their coverage.
The application acts as a strict insurance claims adjudicator, providing clear "Yes" or "No" answers based on the specific exclusions and waiting periods found within the provided policy text. It features a sleek, branded user interface built with Streamlit.
How It Works:
The project consists of two main Python scripts:
1. `app.py` - The Streamlit Web Application
This is the primary, user-facing component of the project.
1.  File Upload & Text Extraction: Users upload one or more policy documents (PDF, DOCX, or TXT) through the sidebar. The application reads the file, extracts the text using libraries like `PyPDF2` and `python-docx`, and stores it in the session state.
2.  User Query: The user selects a document and asks a question about their policy (e.g., "Is my knee surgery covered if I have had the policy for 2 years?").
3.  Context Retrieval: The application intelligently splits the document text into chunks and uses a keyword-matching function (`find_relevant_chunks`) to find the most relevant sections of the policy to answer the user's query.
4.  Prompt Engineering: A detailed prompt is constructed for the Llama 3 model. It instructs the AI to act as a strict claims adjudicator, focusing first on exclusions and waiting periods. The prompt includes the user's question and the most relevant text chunks from the policy as context.
5.  Groq API Call: The prompt is sent to the Groq API, which runs the `llama3-8b-8192` model to generate a response. The application uses a very low temperature (`0.1`) to ensure factual, non-creative answers.
6.  Display Results: The AI's answer is displayed in the main interface, and the conversation is added to a persistent chat history in the sidebar.
2. `ingest.py` - Document Pre-processing for Vector Search
This script is for pre-processing a directory of PDF documents and is intended for building a more advanced, searchable knowledge base using vector embeddings. It is not run by the live Streamlit app but represents an alternative, more scalable backend approach.
1.  Load Documents: It scans a `data/` directory for all PDF files using `PyPDFLoader`.
2.  Split Text: It splits the documents into large, overlapping chunks (`chunk_size=1500`, `chunk_overlap=300`) to maintain context using Langchain's `RecursiveCharacterTextSplitter`.
3.  Create Embeddings: It converts these text chunks into numerical vectors (embeddings) using the `sentence-transformers/all-MiniLM-L6-v2` model from Hugging Face.
4.  Store in VectorDB: It saves these embeddings into a local ChromaDB vector store located in the `db` directory, allowing for efficient semantic search.
Key Features:
  * Multi-Format Document Upload: Supports PDF (`.pdf`), Microsoft Word (`.docx`), and plain text (`.txt`) files.
  * AI-Powered Adjudication: Uses `llama3-8b-8192` via the high-speed Groq API to analyze policy terms.
  * Strict Policy Analysis: The AI is specifically prompted to first identify **exclusions** and **waiting periods** to provide a clear "Yes" or "No" determination before providing an explanation.
  * Interactive Chat Interface: A user-friendly interface with a persistent chat history for tracking conversations.
  * Professional UI: A custom-styled Streamlit application featuring a "glassmorphism" design and branded elements.
  * Vector Ingestion Pipeline: Includes a separate script for creating a persistent vector store from documents for advanced Retrieval-Augmented Generation (RAG).

Setup and Usage
 Prerequisites

  * Python 3.7+
  * A Groq API Key

 Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and activate a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required Python packages:**

    ```bash
    pip install streamlit pypdf2 python-docx groq langchain_community langchain chroma sentence-transformers
    ```

    *Note: The langchain packages are for running `ingest.py`.*

### Running the Application

1.  **Set the API Key:**
    Open the `app.py` file and replace the placeholder with your Groq API key:

    ```python
    # --- IMPORTANT: PASTE YOUR GROQ API KEY HERE ---
    GROQ_API_KEY = "gsk_YourActualGroqApiKeyGoesHere"
    ```

2.  **Launch the Streamlit app:**

    ```bash
    streamlit run app.py
    ```

3.  **Use the App:**

      - Your browser should open to the application's URL.
      - Use the sidebar to upload one or more policy documents.
      - Select a document from the dropdown menu in the main content area.
      - Enter your question in the text area and click "Process Claim".
      - The AI's analysis will appear on the screen.
