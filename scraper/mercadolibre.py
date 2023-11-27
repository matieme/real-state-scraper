import requests
import time
import logging
import re
import pandas as pd
from utils.property import Property
from utils.constants import Constants

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


def extract_numbers(text):
    if text is None:
        return None
    match = re.search(r'\d+', text)
    return int(match.group()) if match else text


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
    property_data = {
        Constants.MERCADOLIBRE_FEATURE_MAPPING.get(attribute.get("id", ""), None): extract_numbers(
            attribute.get("value_name", "0"))
        for attribute in data.get("attributes", [])
        if attribute.get("id", "") in Constants.MERCADOLIBRE_FEATURE_MAPPING
    }

    price = int(data.get("price", 0))
    total_surface = property_data.get(Constants.TOTAL_SURFACE, None)

    sqr_price = price / total_surface
    sqr_price = round(sqr_price, 2)

    age = DataFormatter.clean_age_data(property_data.get(Constants.AGE, 0))

    item = Property(
        data.get("permalink", ""),
        "mercadolibre",
        "USD",
        price,
        "ARS",
        property_data.get(Constants.EXPENSES, 0),
        sqr_price,
        data.get("location", {}).get("neighborhood", {}).get("name", "").lower() + ", " + data.get("location", {}).get(
            "city", {}).get("name", "").lower(),
        data.get("location", {}).get("address_line", "").lower(),
        property_data.get(Constants.TOTAL_SURFACE, None),
        property_data.get(Constants.COVERED_SURFACE, None),
        property_data.get(Constants.ROOMS, None),
        property_data.get(Constants.BEDROOMS, None),
        property_data.get(Constants.BATHROOMS, None),
        property_data.get(Constants.GARAGES, None),
        age,
        property_data.get(Constants.LAYOUT, None),
        property_data.get(Constants.ORIENTATION, None),
    )

    return item.to_dict()


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
    base_url = f"{BASE_URL}/sites/MLA/search?category=MLA401686"
    urls = [f"{base_url}&q={neighborhood}+capital+federal" for neighborhood in NEIGHBORHOODS_CABA]

    ids = get_ids(urls)

    ids_response = get_by_ids(ids)
    df_page = extract_data(ids_response)
    df_page.to_csv(f"results/scraped_mercadolibre.csv", index=False)

    elapsed_time = time.time() - start_time
    logger.info(f"Time taken to get properties from MercadoLibre: {elapsed_time:.2f} seconds")
