import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Define paths and model names
PERSIST_DIRECTORY = 'db'
DATA_PATH = 'data/'
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    """
    Loads PDF documents, splits them into chunks using an optimized strategy,
    creates embeddings, and stores them in a Chroma vector store.
    """
    # 1. Load Documents
    print("Loading documents...")
    documents = []
    for file in os.listdir(DATA_PATH):
        if file.endswith('.pdf'):
            pdf_path = os.path.join(DATA_PATH, file)
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
    print(f"Loaded {len(documents)} pages from PDF files.")

    # 2. Split Documents into Chunks
    print("Splitting documents into chunks...")
    # Using a larger chunk size and overlap to keep related context together
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    texts = text_splitter.split_documents(documents)
    print(f"Split documents into {len(texts)} chunks.")

    # 3. Create Embeddings
    print("Creating embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print("Embeddings model loaded.")

    # 4. Store Chunks in ChromaDB
    print("Storing chunks in ChromaDB vector store...")
    db = Chroma.from_documents(
        texts,
        embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    print(f"--- Ingestion Complete ---")
    print(f"Successfully stored {db._collection.count()} chunks in the '{PERSIST_DIRECTORY}' directory.")

if __name__ == "__main__":
    main()
