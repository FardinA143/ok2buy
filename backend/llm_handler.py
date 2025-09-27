import json
import logging
import os
import re

from classifier import SwissLegalClassifier


def create_classifier() -> SwissLegalClassifier:
    return SwissLegalClassifier()


def llm_query(product_description, legal_fragments, prompt_type):
    """Clasifica un producto dado su descripción y fragmentos legales"""
    classifier = create_classifier()
    if not classifier.client:
        raise ConnectionError(
            "No se pudo conectar con la API. Verifica tu .env")

    return classifier.llm_query(product_description, legal_fragments, prompt_type)


def start_classification(product_info: dict) -> dict:
    # first sanitize and prepare the product name and description
    # convert product_info from dict to a single string
    product_info_str = " ".join(f"{k}: {v}" for k, v in product_info.items())
    product_desc = llm_query(product_info_str, "", "describe")
    # product_desc = llm_query(product_info["product_name"] + ". " + product_info["product_description"], "", "describe")["content"]
    logging.info(f"Product description: {product_desc}")  # debug

    laws = []
    laws_folder = './laws'
    for filename in os.listdir(laws_folder):
        if filename.endswith('.json'):
            with open(os.path.join(laws_folder, filename), 'r', encoding='utf-8') as file:
                laws.append(file.read())
    legal_fragments = "\n".join(laws)

    relevant_laws = llm_query(product_desc, legal_fragments, "laws")
    logging.info(f"Relevant laws: {relevant_laws}")  # debug
    # finally classify the product
    classification_result = llm_query(
        product_desc, legal_fragments, "classify")
    logging.info(f"Classification result: {classification_result}")  # debug
    # return a dict with legality status and reasoning
    try:
        classification_json = json.loads(classification_result)
        list_of_reasoning = classification_json.get(
            "reasoning", "").split(". ")
        return classification_json.get("classification", "unknown"), list_of_reasoning
    except json.JSONDecodeError:
        # Try to clean and validate the output to ensure it's valid JSON

        # Remove any non-JSON text before/after the JSON object
        match = re.search(r'(\{.*\})', classification_result, re.DOTALL)
        if match:
            cleaned_result = match.group(1)
            try:
                classification_json = json.loads(cleaned_result)
                list_of_reasoning = classification_json.get(
                    "reasoning", "").split(". ")
                return classification_json.get("classification", "unknown"), list_of_reasoning
            except Exception:
                raise ValueError(
                    "No se pudo limpiar y validar la respuesta del modelo como JSON.")
        else:
            raise ValueError(
                "La respuesta del modelo no contiene un JSON válido.")
    except Exception as e:
        raise ValueError(f"Error procesando la respuesta del modelo: {e}")
