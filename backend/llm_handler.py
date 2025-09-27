# llm_handler.py (MODIFIED)

import os
import json
from classifier import SwissLegalClassifier
import re
from law_retriever_module import retrieve_laws_for_llm # <-- NEW IMPORT

def create_classifier() -> SwissLegalClassifier:
    return SwissLegalClassifier()

def llm_query(product_description, legal_fragments, prompt_type):
    """Clasifica un producto dado su descripción y fragmentos legales"""
    classifier = create_classifier()
    if not classifier.client:
        raise ConnectionError("No se pudo conectar con la API. Verifica tu .env")

    return classifier.llm_query(product_description, legal_fragments, prompt_type)

def start_classification(product_info: dict) -> dict:
    # first sanitize and prepare the product name and description
    product_info_str = " ".join(f"{k}: {v}" for k, v in product_info.items())
    product_desc = llm_query(product_info_str, "", "describe")
    print(f"Product description: {product_desc}") # debug
    
    # --- RAG / LEGACY LOGIC START ---
    # Now calls the new module to get legal fragments
    legal_fragments = retrieve_laws_for_llm(product_desc) # <-- NEW LINE
    # --- RAG / LEGACY LOGIC END ---
    
    # Note: If running in Legacy mode, 'legal_fragments' contains ALL laws.
    # If running in RAG mode, 'legal_fragments' contains only the TOP N laws.
    
    relevant_laws = llm_query(product_desc, legal_fragments, "laws")
    print(f"Relevant laws: {relevant_laws}") # debug
    
    # finally classify the product
    classification_result = llm_query(product_desc, legal_fragments, "classify")
    print(f"Classification result: {classification_result}") # debug
    
    # return a dict with legality status and reasoning
    try:
        classification_json = json.loads(classification_result)
        list_of_reasoning = classification_json.get("reasoning", "").split(". ")
        return  classification_json.get("classification", "unknown"), list_of_reasoning
    except json.JSONDecodeError:
        # Try to clean and validate the output to ensure it's valid JSON
        match = re.search(r'(\{.*\})', classification_result, re.DOTALL)
        if match:
            cleaned_result = match.group(1)
            try:
                classification_json = json.loads(cleaned_result)
                list_of_reasoning = classification_json.get("reasoning", "").split(". ")
                return classification_json.get("classification", "unknown"), list_of_reasoning
            except Exception:
                raise ValueError("No se pudo limpiar y validar la respuesta del modelo como JSON.")
        else:
            raise ValueError("La respuesta del modelo no contiene un JSON válido.")
    except Exception as e:
        raise ValueError(f"Error procesando la respuesta del modelo: {e}")