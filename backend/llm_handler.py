import json
import logging
import os
import re

from classifier import SwissLegalClassifier


def create_classifier() -> SwissLegalClassifier:
    return SwissLegalClassifier()


def llm_query(product_description, legal_fragments, prompt_type):
    """Classify a product given its description and legal fragments"""
    classifier = create_classifier()
    if not classifier.client:
        raise ConnectionError(
            "Could not connect to the LLM service. "
            "Check your configuration.")

    return classifier.llm_query(product_description, legal_fragments, prompt_type)


def start_classification(product_info: dict) -> dict:
    product_info_str = " ".join(f"{k}: {v}" for k, v in product_info.items())
    product_desc = llm_query(product_info_str, "", "describe")
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

    classification_result = llm_query(
        product_desc, legal_fragments, "classify")
    logging.info(f"Classification result: {classification_result}")  # debug
    try:
        classification_json = json.loads(classification_result)
        list_of_reasoning = classification_json.get(
            "reasoning", "").split(". ")
        return classification_json.get("classification", "unknown"), list_of_reasoning
    except json.JSONDecodeError:

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
                    "Could not process the response correctly.")
        else:
            raise ValueError(
                "Could not find a valid response object.")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")
