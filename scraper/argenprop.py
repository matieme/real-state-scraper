from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from tqdm import tqdm

# Global constants
START_PAGE = 2
MAX_PAGES = 10
RETRIES = 3
BASE_URL = "https://www.argenprop.com"

HEADERS = {
    'authority': 'www.argenprop.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9,es-US;q=0.8,es;q=0.7',
    'cache-control': 'max-age=0',
    'cookie': '_gcl_au=1.1.915058023.1696996656; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22jlgty5cYVRTfRmf7QASw%22%7D; _gid=GA1.3.909566837.1696996656; sessionId=719d2a39-3b0c-4003-8780-fd99339b799b; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%7D; _fbp=fb.2.1696996656597.2087731844; _hjSessionUser_194887=eyJpZCI6ImM4ODc0NjhlLTdmNmQtNTE0Yi1iNmU4LWQzYTYyMWJiYzlkOCIsImNyZWF0ZWQiOjE2OTY5OTY2NTY4MTMsImV4aXN0aW5nIjp0cnVlfQ==; __cf_bm=ZKDgzS1o3fx68DUge6PTgHPu7W42Z9NZzLZYCo9g_SA-1697064859-0-AbMXnhffFxiKcMKE6zQeZuA86b7uKrq7JujXDFrYGLBd9SODuOWmiQx2UCaN2QlwUMNETHmIJ1tZ1eX+fbT0Go60I5FMC5aLzOihKV/ED2mS; _dc_gtm_UA-5217585-1=1; cf_clearance=6NEqR9IScjs6l2qXwhqj7A_wuD6aRMQklUcebxGwg5Y-1697064860-0-1-5a96a806.f237fc96.d300f59c-160.2.1697064860; __gads=ID=ee8269041c5e1324:T=1696996656:RT=1697064860:S=ALNI_MZb-zqUx8CHbjVpcEZg2AU8mPWB5Q; __gpi=UID=00000a17b9f09a29:T=1696996656:RT=1697064860:S=ALNI_MZL2WqEfjo5_Gir3Mtb2pe5R20Ntw; _hjIncludedInSessionSample_194887=0; _hjSession_194887=eyJpZCI6ImQyMmUyMWE5LTZiYzUtNDhmMy1iNmFhLTg0OGVkODJmZGIwMiIsImNyZWF0ZWQiOjE2OTcwNjQ4NTg0NjcsImluU2FtcGxlIjpmYWxzZSwic2Vzc2lvbml6ZXJCZXRhRW5hYmxlZCI6ZmFsc2V9; _hjAbsoluteSessionInProgress=1; _ga=GA1.3.392380778.1696996656; _ga_68T3PL08E4=GS1.1.1697064858.3.0.1697064859.59.0.0; JSESSIONID=4B7A8D2F1B38493306CF41E2B3CE4342',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
}

FEATURE_MAPPING = {
    "icono-superficie_total": "Total Surface",
    "icono-superficie_cubierta": "Covered Surface",
    "icono-cantidad_ambientes": "Rooms",
    "icono-cantidad_dormitorios": "Bedrooms",
    "icono-cantidad_banos": "Bathrooms",
    "icono-ambiente_cochera": "Garages"
}

context = None


def parse_item(url, div, div_item):
    card_price = div.select_one('p.card__price')
    price = None
    if card_price and not card_price.select_one('.card__noprice'):
        currency = card_price.select_one('.card__currency').text.strip()
        price_value = card_price.contents[2]
        price = f"{currency} {clean_data(price_value)}"

    # location = div.select_one('.card__address').get_text().strip()
    location_container = div.select('.card__monetary-values')
    location = location_container[0].contents[7].get_text()

    features = div.select('.card__main-features>li')

    item_features = div_item.select('.property-main-features>li')

    feature_data = extract_feature_data(features)
    complete_data = extract_item_feature_data(item_features, feature_data)

    item = {
        "Referencia": url,
        "Price": price,
        "Location": location,
        "Total Surface": complete_data["Total Surface"] if complete_data.get("Total Surface") else complete_data["Covered Surface"],
        "Covered Surface": complete_data["Covered Surface"] if complete_data.get("Covered Surface") else None,
        "Rooms": complete_data["Rooms"] if complete_data.get("Rooms") else None,
        "Bedrooms": complete_data["Bedrooms"] if complete_data.get("Bedrooms") else None,
        "Bathrooms": complete_data["Bathrooms"] if complete_data.get("Bathrooms") else None,
        "Garages": complete_data["Garages"] if complete_data.get("Garages") else None,
    }

    return item


def extract_feature_data(features):
    extracted_data = {}
    for feature in features:
        value = feature.get_text()
        icon_class = feature.select_one('i')['class'][0]
        if icon_class in FEATURE_MAPPING:
            extracted_data[FEATURE_MAPPING[icon_class]] = clean_data(value)
    return extracted_data


def extract_item_feature_data(item_features, existing_data):
    for item_feature in item_features:
        value = item_feature.get_text()
        title_class = item_feature.select_one('i')['class'][0]
        if title_class in FEATURE_MAPPING and not existing_data.get(FEATURE_MAPPING[title_class]):
            existing_data[FEATURE_MAPPING[title_class]] = clean_item_data(value)
    return existing_data


def extract_data(soup, page, page_link):
    container_div = soup.find('div', class_='listing__items')

    for _ in range(RETRIES):
        if container_div:
            break
        print("No postings-container found in the page. Retrying...")
        time.sleep(5)
        page.goto(page_link)
        soup = BeautifulSoup(page.content(), 'lxml')
        container_div = soup.find('div', class_='listing__items')

    if not container_div:
        print("Failed to find postings-container after retries.")
        return pd.DataFrame()

    results = []

    for i, tag in enumerate(container_div.contents):
        try:
            if tag:
                url = tag.find('a')['href']
                item = parse_item(url, tag, get_child_item_data(url))
                # print(item)
                results.append(item)
        except Exception as e:
            print(e)
            pass

    return pd.DataFrame(results)


def get_child_item_data(url):
    new_page_link_item = BASE_URL + url
    page_item, soup_item = open_new_page(new_page_link_item)
    container_div_item = soup_item.find('div', class_='property-description')
    return container_div_item


def clean_data(data_str):
    return data_str.replace("\n", "").strip()


def clean_item_data(data_str):
    match = re.search(r'(\S[^\n]*\S)', data_str)
    return match.group(1) if match else ""


def open_new_page(page_link):
    global context
    page = context.new_page()

    page.set_extra_http_headers(HEADERS)

    print(page_link)

    try:
        page.goto(page_link)
    except:
        page.goto(page_link)
    html = page.content()
    soup = BeautifulSoup(html, 'lxml')
    return page, soup


def run():
    global context
    with sync_playwright() as p:
        for current_page in tqdm(range(START_PAGE, MAX_PAGES + 1)):
            browser = p.chromium.launch(headless=False)

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            )

            page_link = f'https://www.argenprop.com/departamentos/venta/capital-federal/pagina-{current_page}.html'
            page, soup = open_new_page(page_link)
            df_page = extract_data(soup, page, page_link)

            df_page.to_csv(f"results/scraped_argenprop_page_{current_page}.csv", index=False)

            browser.close()  # Close browser after processing each page

            time.sleep(2)  # Add a delay after closing the browser before opening a new one for the next URL
