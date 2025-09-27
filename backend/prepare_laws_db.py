# prepare_laws_db.py

import os
import json
import chromadb
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
MODEL_NAME = "all-MiniLM-L6-v2" # Recommended for speed; consider 'all-mpnet-base-v2' for better precision
LOCAL_MODEL_PATH = "./custom_law_model" 
JSON_FOLDER = "laws" # Assuming your law JSONs are in a folder named 'laws'
DB_PATH = "laws_db"
COLLECTION_NAME = "laws_collection"

# --- UTILITY FUNCTION FOR DYNAMIC FIELDS ---

def _extract_nested_info(data: Dict[str, Any], prefix: str = "") -> List[str]:
    """Recursively extracts information from nested dictionaries into a list of strings."""
    info_lines = []
    for key, value in data.items():
        clean_key = key.replace('_', ' ').title()
        
        if isinstance(value, dict):
            info_lines.extend(_extract_nested_info(value, prefix=f"{prefix}{clean_key} - "))
        elif isinstance(value, list):
            info_lines.append(f"{prefix}{clean_key}: {'; '.join(map(str, value))}")
        elif isinstance(value, str) and value.strip():
            info_lines.append(f"{prefix}{clean_key}: {value}")
            
    return info_lines

# --- JSON PREPROCESSING FUNCTION (MAIN) ---

def json_to_law_text(json_data: Dict[str, Any]) -> List[str]:
    """Integrates header, item details, and footer notes into a structured law text."""
    law_texts = []
    root_key = list(json_data.keys())[0]
    parts = root_key.split('_')
    theme = parts[0].title()
    law_class = parts[1].title()
    top_level_data = json_data[root_key]

    # Extract Dynamic Header Context 
    header_context_lines = []
    for key, value in top_level_data.items():
        if key in ['classification', 'important_notes']:
            continue
        if isinstance(value, dict):
            header_context_lines.extend(_extract_nested_info(value))
        elif isinstance(value, str) and value.strip():
            header_context_lines.append(f"{key.replace('_', ' ').title()}: {value}")
            
    header_context = " | ".join(header_context_lines)
    
    # Extract Dynamic Footer Notes ('important_notes')
    footer_notes = []
    important_notes_data = top_level_data.get('important_notes', {})
    if important_notes_data:
        footer_notes.extend(_extract_nested_info(important_notes_data))
    
    footer_context = " | ".join(footer_notes)
    
    # Generate text for each item
    items = top_level_data.get('classification', {}).get('items', [])

    for item in items:
        category = item.get('category', 'Rule Detail').strip()
        
        law_text = f"CUSTOMS LAW DOCUMENT: {category}. "
        law_text += f"TOPIC: {theme}. CLASS: {law_class}. "
        
        if header_context:
            law_text += f"GENERAL REGULATION: {header_context}. "
        
        for field, value in item.items():
            if field == 'category': 
                continue
            field_name = field.replace('_', ' ').title()
            
            if isinstance(value, list):
                value_text = '; '.join([str(v) for v in value])
                law_text += f"{field_name} (List): {value_text}. "
            elif isinstance(value, str) and value.strip():
                law_text += f"{field_name}: {value}. "
        
        if footer_context:
            law_text += f"IMPORTANT NOTES/WARNINGS: {footer_context}. "
            
        law_texts.append(law_text.strip())

    return law_texts

# --- MAIN EXECUTION ---

def create_laws_vector_db():
    """
    Loads the model, reads JSONs, generates embeddings, and inserts them into ChromaDB.
    """
    print(f"🤖 Loading embedding model: {MODEL_NAME}...")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"ERROR: Could not load model. {e}")
        return

    all_laws_to_add = []
    
    if not os.path.exists(JSON_FOLDER):
        print(f"⚠️ JSON folder '{JSON_FOLDER}' not found.")
        return

    print(f"\n📂 Processing files in folder: {JSON_FOLDER}...")
    for filename in os.listdir(JSON_FOLDER):
        if filename.endswith(".json"):
            file_path = os.path.join(JSON_FOLDER, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                law_texts = json_to_law_text(json_data)
                all_laws_to_add.extend(law_texts)
            except Exception as e:
                print(f"   ⚠️ Error processing {filename}: {e}")

    if not all_laws_to_add:
        print("\n⚠️ No laws found to add.")
        return

    client = chromadb.PersistentClient(path=DB_PATH)
    try:
         client.delete_collection(name=COLLECTION_NAME)
    except:
        pass 
        
    collection = client.get_or_create_collection(COLLECTION_NAME)
    
    ids = [f"law_{i}" for i in range(len(all_laws_to_add))]
    documents = all_laws_to_add
    
    print(f"\n🧠 Generating embeddings for {len(all_laws_to_add)} laws and inserting into DB...")
    embeddings = model.encode(documents, convert_to_tensor=False).tolist()
        
    collection.add(ids=ids, documents=documents, embeddings=embeddings)
    print(f"\n✅ Added {len(all_laws_to_add)} laws to the database ('{DB_PATH}').")
    
    # Save the model used for embedding
    model.save(LOCAL_MODEL_PATH)
    print(f"✅ Embedding model saved to: {LOCAL_MODEL_PATH}")

if __name__ == "__main__":
    create_laws_vector_db()