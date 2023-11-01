﻿import requests
import time
import logging
import re
import pandas as pd

BASE_URL = "https://api.mercadolibre.com"
logger = logging.getLogger()

NEIGHBORHOODS_CABA = [
    "Agronomia", "Almagro", "Balvanera", "Barracas", "Belgrano", "Boedo", "Caballito",
    "Chacarita", "Coghlan", "Colegiales", "Constitucion", "Flores", "Floresta", "La%20Boca",
    "La%20Paternal", "Liniers", "Mataderos", "Monte%20Castro", "Monserrat", "Nueva%20Pompeya",
    "Nunez", "Palermo", "Parque%20Avellaneda", "Parque%20Chacabuco", "Parque%20Chas",
    "Parque%20Patricios", "Puerto%20Madero", "Recoleta", "Retiro", "Saavedra", "San%20Cristobal",
    "San%20Nicolas", "San%20Telmo", "Velez%20Sarsfield", "Versalles", "Villa%20Crespo",
    "Villa%20del%20Parque", "Villa%20Devoto", "Villa%20General%20Mitre", "Villa%20Lugano",
    "Villa%20Luro", "Villa%20Ortuzar", "Villa%20Pueyrredon", "Villa%20Real", "Villa%20Riachuelo",
    "Villa%20Santa%20Rita", "Villa%20Soldati", "Villa%20Urquiza"
]


def get_api_response(url):
    response = requests.get(url)
    response.raise_for_status()
    return response


def chunks(input_list: list, chunk_size: int):
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]


def to_number(str: str):
    try:
        return int(re.sub(r'[^0-9]', '', str))
    except:
        return 0


def get_ids(urls: list[str]):
    ids = []
    for url in urls:
        offset = 0
        max_results = 1
        while offset <= max_results:
            try:
                api_response = get_api_response(url + f"&offset={offset}")
                json_data = api_response.json()
                ids.extend([x.get("id", "") for x in json_data["results"]])
            except Exception as e:
                logger.error(f"Error getting ids from {url} with offset {offset}: {e}")

            max_results = min(json_data["paging"]["total"], 1000) if max_results == 1 else max_results
            offset += 50
    return ids


def get_by_ids(ids):
    # Split ids in chunks of 20 because the API only allows 20 ids per request
    urls = [f"{BASE_URL}/items?ids={','.join(ids_chunk)}" for ids_chunk in chunks(ids, 20)]
    properties_data = []

    for url in urls:
        try:
            api_response = get_api_response(url)
            response_json = api_response.json()
            properties_data.extend(response_json)
        except Exception as e:
            logger.error(f"Error getting response from MercadoLibre: {e}")

    return properties_data


def parse_properties(data: dict):
    attributes = data.get("attributes", [])
    property_data = {}

    for attribute in attributes:
        attr_id = attribute.get("id", "")
        value = to_number(attribute.get("value_name", "0"))
        if attr_id == "ROOMS":
            property_data["Rooms"] = value
        elif attr_id == "BEDROOMS":
            property_data["Bedrooms"] = value
        elif attr_id == "FULL_BATHROOMS":
            property_data["Bathrooms"] = value
        elif attr_id == "TOTAL_AREA":
            property_data["Total Surface"] = value
        elif attr_id == "COVERED_AREA":
            property_data["Covered Surface"] = value
        elif attr_id == "PARKING_LOTS":
            property_data["Garages"] = value

    item = {
        "Referencia": data.get("permalink", ""),
        "Price": int(data.get("price", 0)),
        "Location": data.get("location", {}).get("neighborhood", {}).get("name", "").upper(),
        "Total Surface": property_data["Covered Surface"] if property_data.get("Covered Surface") else None,
        "Covered Surface": property_data["Covered Surface"] if property_data.get("Covered Surface") else None,
        "Rooms": property_data["Rooms"] if property_data.get("Rooms") else None,
        "Bedrooms": property_data["Bedrooms"] if property_data.get("Bedrooms") else None,
        "Bathrooms": property_data["Bathrooms"] if property_data.get("Bathrooms") else None,
        "Garages": property_data["Garages"] if property_data.get("Garages") else None,
    }

    return item


def extract_data(ids_response):
    results = []
    for prop in ids_response:
        try:
            property_data = parse_properties(prop["body"])
            results.append(property_data)
        except Exception as e:
            logger.error(f"Error parsing property from MercadoLibre: {e}")
    return pd.DataFrame(results)


def run():
    start_time = time.time()
    base_url = f"{BASE_URL}/sites/MLA/search?category=MLA1473"
    urls = [f"{base_url}&q={neighborhood}+capital+federal" for neighborhood in NEIGHBORHOODS_CABA]

    ids = get_ids(urls)

    ids_response = get_by_ids(ids)
    df_page = extract_data(ids_response)
    df_page.to_csv(f"results/scraped_mercadolibre.csv", index=False)

    elapsed_time = time.time() - start_time
    logger.info(f"Time taken to get properties from MercadoLibre: {elapsed_time:.2f} seconds")