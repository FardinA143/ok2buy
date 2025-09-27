# law_retriever_module.py

import os
import json
import chromadb
from typing import List
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
LOCAL_MODEL_PATH = "./custom_law_model"
DB_PATH = "laws_db"
COLLECTION_NAME = "laws_collection"
LAWS_FOLDER = "./laws" # Folder used by the legacy system

# --- GLOBAL VARIABLES ---
# The LLM Handler will decide which mode to use. Default to RAG (new mode).
RETRIEVAL_MODE = os.environ.get("LAW_RETRIEVAL_MODE", "RAG").upper() 

# --- RAG Setup (Load model and DB once) ---
try:
    if RETRIEVAL_MODE == "RAG":
        print(f"--- RAG Mode Active: Loading model and DB ---")
        model = SentenceTransformer(LOCAL_MODEL_PATH)
        client = chromadb.PersistentClient(path=DB_PATH)
        laws_collection = client.get_collection(COLLECTION_NAME)
        print(f"--- RAG Setup Complete. DB contains {laws_collection.count()} docs. ---")
    else:
        print(f"--- Legacy Mode Active: Will load all JSONs on demand ---")
except Exception as e:
    # If RAG fails (e.g., DB not created yet), default to Legacy.
    print(f"WARNING: RAG Setup failed ({e}). Defaulting to Legacy Mode.")
    RETRIEVAL_MODE = "LEGACY"
    
# --- RETRIEVER FUNCTIONS ---

def retrieve_laws_for_llm(product_description: str, max_laws: int = 5) -> str:
    """
    Retrieves legal fragments based on the current mode (RAG or Legacy).
    
    In RAG mode, it queries ChromaDB for the most relevant laws.
    In Legacy mode, it loads all laws from the JSON folder.
    """
    if RETRIEVAL_MODE == "RAG":
        return _retrieve_via_vectordb(product_description, max_laws)
    else:
        return _retrieve_via_legacy_mode()

def _retrieve_via_vectordb(query: str, n_results: int) -> str:
    """Retrieves relevant laws from ChromaDB."""
    try:
        query_embedding = model.encode(query, convert_to_tensor=False).tolist()
        
        results = laws_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Join the relevant documents into a single string for the LLM
        if results["documents"] and results["documents"][0]:
            print(f"--- RAG: Retrieved {len(results['documents'][0])} relevant laws. ---")
            return "\n---\n".join(results["documents"][0])
        else:
            return "No specific legal fragments found for this product."
            
    except Exception as e:
        print(f"ERROR during VectorDB retrieval: {e}. Falling back to Legacy mode.")
        return _retrieve_via_legacy_mode()


def _retrieve_via_legacy_mode() -> str:
    """Loads ALL laws from the JSON folder."""
    laws = []
    if not os.path.exists(LAWS_FOLDER):
        print(f"WARNING: Laws folder '{LAWS_FOLDER}' not found for Legacy mode.")
        return ""
        
    for filename in os.listdir(LAWS_FOLDER):
        if filename.endswith('.json'):
            with open(os.path.join(LAWS_FOLDER, filename), 'r', encoding='utf-8') as file:
                # In Legacy mode, we send the raw JSON content to the LLM
                laws.append(file.read())
                
    print(f"--- LEGACY: Loaded {len(laws)} files (ALL laws). ---")
    return "\n".join(laws)