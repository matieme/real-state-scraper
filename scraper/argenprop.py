from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from tqdm import tqdm
from utils.property import Property
from utils.constants import Constants
from utils.configloader import load_config
from utils.dataformatter import DataFormatter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Global constants
START_PAGE = 2
MAX_PAGES = 10
RETRIES = 3

context = None
config = None


def parse_item(url, div, div_item):
    card_price = div.select_one('p.card__price')
    price = 0
    price_currency = 0
    if card_price and not card_price.select_one('.card__noprice'):
        price_currency = card_price.select_one('.card__currency').text.strip()
        price = DataFormatter.extract_int_value(DataFormatter.clean_data(card_price.contents[2]))

    location_container = div.select('.card__monetary-values')
    location = location_container[0].contents[7].get_text().lower()

    exact_direction = DataFormatter.clean_data(location_container[0].contents[3].get_text()).lower()
    expenses = DataFormatter.extract_int_value(div.select_one('span.card__expenses').get_text()) if div.select_one(
        'span.card__expenses') else 0

    item_features = div_item.select('.property-main-features>li')

    complete_data = extract_feature_data(item_features)

    total_surface = complete_data[Constants.TOTAL_SURFACE] if complete_data.get(Constants.TOTAL_SURFACE) else \
        complete_data[
            Constants.COVERED_SURFACE]

    sqr_price = price / total_surface
    sqr_price = round(sqr_price, 2)

    covered_surface = complete_data.get(Constants.COVERED_SURFACE) if complete_data.get(
        Constants.COVERED_SURFACE) else complete_data.get(Constants.TOTAL_SURFACE)
    rooms = clean_rooms_data(complete_data.get(Constants.ROOMS))
    bedrooms = complete_data.get(Constants.BEDROOMS) if complete_data.get(Constants.BEDROOMS) is not None else 0
    bathrooms = complete_data.get(Constants.BATHROOMS) if complete_data.get(Constants.BATHROOMS) is not None else 0
    garages = complete_data.get(Constants.GARAGES) if complete_data.get(Constants.GARAGES) is not None else 0

    item = Property(
        url,
        "argenprop",
        price_currency,
        price,
        'ARS',
        expenses,
        sqr_price,
        location,
        exact_direction,
        total_surface,
        covered_surface,
        rooms,
        bedrooms,
        bathrooms,
        garages,
        complete_data.get(Constants.AGE),
        clean_repeated_words(complete_data.get(Constants.LAYOUT)),
        clean_repeated_words(complete_data.get(Constants.ORIENTATION)),
    )

    return item.to_dict()


def clean_rooms_data(rooms):
    if rooms is None or rooms == 0 or isinstance(rooms, str):
        return 1
    return rooms


def extract_feature_data(features):
    extracted_data = {}
    for feature in features:
        value = feature.get_text()
        icon_class = feature.select_one('i')['class'][0]
        if icon_class in Constants.ARGENPROP_FEATURE_MAPPING:
            extracted_data[Constants.ARGENPROP_FEATURE_MAPPING[icon_class]] = extract_numbers(
                DataFormatter.clean_data(value))
    return extracted_data


def extract_numbers(text):
    if text is None:
        return None
    match = re.search(r'\d+', text)
    return int(match.group()) if match else text


def extract_data(soup, page, page_link):
    container_div = soup.find('div', class_='listing__items')

    for _ in range(RETRIES):
        if container_div:
            break
        logger.warning("No postings-container found in the page. Retrying...")
        time.sleep(5)
        page.goto(page_link)
        soup = BeautifulSoup(page.content(), 'lxml')
        container_div = soup.find('div', class_='listing__items')

    if not container_div:
        logger.warning("Failed to find postings-container after retries.")
        return pd.DataFrame()

    results = []

    for i, tag in enumerate(container_div.contents):
        try:
            if tag:
                url = tag.find('a')['href']
                item = parse_item(url, tag, get_child_item_data(url))
                results.append(item)
        except Exception as e:
            logger.error(e)
            pass

    return pd.DataFrame(results)


def get_child_item_data(url):
    new_page_link_item = config["BASE_URL"] + url
    page_item, soup_item = open_new_page(new_page_link_item)
    time.sleep(1)
    container_div_item = soup_item.find('div', class_='property-description')
    return container_div_item


def clean_repeated_words(data_str: str) -> str:
    if data_str is None:
        return None
    words = data_str.split()
    seen = {}
    for word in words:
        lw = word.lower()
        if lw not in seen:
            seen[lw] = word
    return ' '.join(seen.values())


def open_new_page(page_link):
    global context
    page = context.new_page()

    page.set_extra_http_headers(config["HEADERS"])

    logger.info(page_link)

    try:
        page.goto(page_link)
    except:
        page.goto(page_link)
    html = page.content()
    soup = BeautifulSoup(html, 'lxml')
    return page, soup


def run():
    global context
    global config

    config = load_config("scraper/configs/argenprop-config.json")
    with sync_playwright() as p:
        for current_page in tqdm(range(START_PAGE, MAX_PAGES + 1)):
            browser = p.chromium.launch(headless=False)

            context = browser.new_context(user_agent=config["HEADERS"]["user-agent"])

            page_link = f'{config["BASE_URL"]}/departamentos/venta/capital-federal/pagina-{current_page}'
            page, soup = open_new_page(page_link)
            df_page = extract_data(soup, page, page_link)

            df_page.to_csv(f"results/scraped_argenprop_page_{current_page}.csv", index=False)

            browser.close()  # Close browser after processing each page

            time.sleep(3)  # Add a delay after closing the browser before opening a new one for the next URL
