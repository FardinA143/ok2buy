import json
import logging

ignore_fields = ["image", "product_mall_id", "image_urls",
                 "video_urls", "image_urls_downloaded", "product_sn"]


def load_products_json() -> list:
    with open('./data/ecommerce_labels.json', 'r', encoding="utf-8") as file:
        data = json.load(file)
        logging.info(f"Loaded {len(data)} products from JSON.")
        return data


def get_product_info(product_id: int) -> dict:
    response = load_products_json()
    product_id_str = str(product_id)

    product = next(
        (p for p in response if p["product_code"] == product_id_str), None)

    if product is None:
        logging.info(f"Product ID {product_id} not found in data.")
        raise ValueError(f"Product ID {product_id} not found in data.")

    else:
        cleaned_response = {k: v for k,
                            v in product.items() if k not in ignore_fields}
    return cleaned_response
