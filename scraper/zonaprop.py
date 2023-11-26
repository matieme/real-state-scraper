from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
from utils.property import Property
from utils.constants import Constants
from utils.configloader import load_config
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

# Global constants
START_PAGE = 2
MAX_PAGES = 10
RETRIES = 3

context = None


def parse_item(url, div):
    container = div.select('.clearfix')
    price = extract_text_and_remove(container[2].select_one('.price-value').text.strip(), 'USD')
    expenses_element = container[2].select_one('.price-expenses')
    if expenses_element is None:
        expenses = None
    else:
        expenses = extract_currency_amount(expenses_element.text.strip())

    full_location = container[2].select_one('.section-location-property').text.strip()
    parts = full_location.split(',', 1)

    exact_location = parts[0].strip() if parts else None
    location = parts[1].strip() if len(parts) > 1 else None

    features = div.select('.section-icon-features-property>li')

    feature_data = extract_feature_data(features)

    item = Property(
        url,
        "ZONA PROPS",
        price,
        expenses,
        location,
        exact_location,
        feature_data.get(Constants.TOTAL_SURFACE),
        feature_data.get(Constants.COVERED_SURFACE),
        feature_data.get(Constants.ROOMS),
        feature_data.get(Constants.BEDROOMS),
        feature_data.get(Constants.BATHROOMS),
        feature_data.get(Constants.GARAGES),
        feature_data.get(Constants.AGE),
        feature_data.get(Constants.LAYOUT),
        feature_data.get(Constants.ORIENTATION),
    )

    return item.to_dict()


def extract_feature_data(features):
    extracted_data = {}
    for feature in features:
        value = feature.get_text()
        icon_class = feature.select_one('i')['class'][0]
        if icon_class in Constants.ZONAPROP_FEATURE_MAPPING:
            extracted_data[Constants.ZONAPROP_FEATURE_MAPPING[icon_class]] = extract_numbers(clean_data(value))
    return extracted_data


def extract_text_and_remove(text, text_to_remove):
    parts = [part.strip() for part in text.split('\n') if part.strip() and text_to_remove in part]
    return parts[0] if parts else text


def clean_data(data_str):
    return data_str.replace("\n", "").strip()


def extract_numbers(text):
    if text is None:
        return None
    match = re.search(r'\d+', text)
    return int(match.group()) if match else text


def extract_currency_amount(text):
    currency_amounts = re.findall(r'\$\s*\d+(?:\.\d+)?', text)
    return currency_amounts[0] if currency_amounts else None


def extract_data(soup, page, page_link):
    container_div = soup.find('div', class_='postings-container')

    for _ in range(RETRIES):
        if container_div:
            break
        print("No postings-container found in the page. Retrying...")
        time.sleep(5)
        page.goto(page_link)
        soup = BeautifulSoup(page.content(), 'lxml')
        container_div = soup.find('div', class_='postings-container')

    if not container_div:
        print("Failed to find postings-container after retries.")
        return pd.DataFrame()

    results = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for i, div in enumerate(container_div.contents):
            if div:
                url = div.find('a')['href']
                time.sleep(2)
                future = executor.submit(run_async_in_thread, get_child_item_data, url)
                futures.append((future, url))

        for future, url in futures:
            try:
                item_container = future.result()
                if item_container:
                    print(url)
                    item = parse_item(url, item_container)
                    results.append(item)
            except Exception as e:
                print(e)

    return pd.DataFrame(results)


async def get_child_item_data(url):
    config = load_config("scraper/configs/zonaprop-config.json")
    new_page_link_item = config["BASE_URL"] + url

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=config["HEADERS"]["user-agent"])

        page = await context.new_page()
        await page.set_extra_http_headers(config["HEADERS"])

        try:
            await page.goto(new_page_link_item)
            time.sleep(1)
            html_content = await page.content()
            soup_item = BeautifulSoup(html_content, 'lxml')

            container_div_item = soup_item.find('div', class_='main-container-property')
        except Exception as e:
            print(f"Failed to load {new_page_link_item}: {e}")
        finally:
            await browser.close()

        return container_div_item


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


def run_async_in_thread(async_func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(async_func(*args))
    time.sleep(2)
    loop.close()
    return result


def run():
    global context
    global config

    config = load_config("scraper/configs/zonaprop-config.json")
    with sync_playwright() as p:
        for current_page in tqdm(range(START_PAGE, MAX_PAGES + 1)):
            browser = p.chromium.launch(headless=False)

            context = browser.new_context(user_agent=config["HEADERS"]["user-agent"])

            page_link = f'{config["BASE_URL"]}/inmuebles-venta-capital-federal-pagina-{current_page}.html'
            time.sleep(1)
            page, soup = open_new_page(page_link)
            df_page = extract_data(soup, page, page_link)

            df_page.to_csv(f"results/scraped_zonaprop_page_{current_page}.csv", index=False)

            browser.close()  # Close browser after processing each page

            time.sleep(3)  # Add a delay after closing the browser before opening a new one for the next URL
