from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from tqdm import tqdm
from utils.property import Property
from utils.constants import Constants
from utils.configloader import load_config

# Global constants
START_PAGE = 2
MAX_PAGES = 10
RETRIES = 3

context = None
config = None


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

    exact_direction = clean_data(location_container[0].contents[3].get_text())
    expenses = clean_item_data(div.select_one('span.card__expenses').get_text())

    item_features = div_item.select('.property-main-features>li')

    feature_data = extract_feature_data(features)
    complete_data = extract_item_feature_data(item_features, feature_data)

    item = Property(
        url,
        "ARGENPROP",
        price,
        expenses,
        location,
        exact_direction,
        complete_data[Constants.TOTAL_SURFACE] if complete_data.get(Constants.TOTAL_SURFACE) else complete_data[
            Constants.COVERED_SURFACE],
        complete_data.get(Constants.COVERED_SURFACE),
        complete_data.get(Constants.ROOMS),
        complete_data.get(Constants.BEDROOMS),
        complete_data.get(Constants.BATHROOMS),
        complete_data.get(Constants.GARAGES),
        complete_data.get(Constants.AGE),
        complete_data.get(Constants.LAYOUT),
        complete_data.get(Constants.ORIENTATION),
    )

    return item.to_dict()


def extract_feature_data(features):
    extracted_data = {}
    for feature in features:
        value = feature.get_text()
        icon_class = feature.select_one('i')['class'][0]
        if icon_class in Constants.ARGENPROP_FEATURE_MAPPING:
            extracted_data[Constants.ARGENPROP_FEATURE_MAPPING[icon_class]] = extract_numbers(clean_data(value))
    return extracted_data


def extract_item_feature_data(item_features, existing_data):
    for item_feature in item_features:
        value = item_feature.get_text()
        title_class = item_feature.select_one('i')['class'][0]
        if title_class in Constants.ARGENPROP_FEATURE_MAPPING and not existing_data.get(
                Constants.ARGENPROP_FEATURE_MAPPING[title_class]):
            existing_data[Constants.ARGENPROP_FEATURE_MAPPING[title_class]] = clean_item_data(value)
    return existing_data


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
                results.append(item)
        except Exception as e:
            print(e)
            pass

    return pd.DataFrame(results)


def get_child_item_data(url):
    new_page_link_item = config["BASE_URL"] + url
    page_item, soup_item = open_new_page(new_page_link_item)
    time.sleep(1)
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

    page.set_extra_http_headers(config["HEADERS"])

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
