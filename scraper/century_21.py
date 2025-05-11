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
from datetime import datetime, timezone
from services.scraper_service import ScraperService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

START_PAGE = 1
MAX_PAGES = 1
RETRIES = 3

context = None
config = None


def extract_property_id(url: str) -> str:
    match = re.search(r'/propiedad/(\d+)_', url)
    return match.group(1) if match else ''


def extract_rooms_from_icons(soup):
    try:
        icon = soup.find('i', class_='far fa-check-square')
        if not icon:
            return 1
        div = icon.find_parent('div')
        if not div:
            return 1
        span = div.find('span')
        if not span:
            return 1
        rooms_text = span.get_text(strip=True)
        rooms = safe_int(rooms_text)
        return rooms
    except Exception as e:
        logger.warning(f"Could not extract rooms: {e}")
        return 1  # default


def extract_age_from_icons(soup):
    try:
        icon = soup.find('i', class_='fal fa-clock')
        if not icon:
            return None
        li = icon.find_parent('div')
        if not li:
            return None
        span = li.find('span', class_='fw-bold')
        if not span:
            return None

        construction_text = span.get_text(strip=True)
        return DataFormatter.clean_age_data(construction_text)

    except (ValueError, TypeError) as e:
        logger.warning(f"Could not extract age: {e}")
        return None



def parse_item(url, soup, page):
    property_id = extract_property_id(url)
    source_name = "century21"
    source_identifier = f"{source_name}-{property_id}" if property_id else None
    scrape_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_meta_content(name):
        tag = soup.find('meta', {'name': name})
        return tag['content'] if tag else None

    price = DataFormatter.extract_int_value(get_meta_content('precio'))
    price_currency = get_meta_content('moneda')
    expenses = None
    expenses_currency = None

    # Default values for Argentina
    country = "Argentina"
    state = "Buenos Aires"
    city = "Capital Federal"

    # Extract address and zone
    full_direction = get_meta_content('direccion').strip()
    parts = full_direction.split(',', 1)
    address = parts[0].strip() if parts else None

    # Get zone from meta content
    zone = get_meta_content('municipio')

    total_surface = DataFormatter.extract_int_value(get_meta_content('MT'))
    covered_surface = DataFormatter.extract_int_value(get_meta_content('MC'))
    rooms = extract_rooms_from_icons(soup)
    bedrooms = safe_int(get_meta_content('recamaras') or 1)
    bathrooms = safe_int(get_meta_content('banio') or 0)
    garages = safe_int(get_meta_content('estacionamiento') or 0)
    sqr_price = round(price / total_surface, 2) if price and total_surface else 0

    age = extract_age_from_icons(soup)

    latitude, longitude = extract_lat_lon_via_click(page)

    layout = None
    if layout:
        layout = layout.lower()
        layout = Constants.LAYOUT_MAPPING.get(layout, layout)
    orientation = None
    if orientation:
        orientation = orientation.lower()
        orientation = Constants.ORIENTATION_MAPPING.get(orientation, orientation)

    item = Property(
        url=url,
        source_name=source_name,
        source_identifier=source_identifier,
        scrape_date=scrape_date,
        price_currency=price_currency,
        price=price,
        expenses_currency=expenses_currency,
        expenses=expenses,
        sqr_price=sqr_price,
        total_surface=total_surface,
        covered_surface=covered_surface,
        rooms=rooms,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        garages=garages,
        layout=layout,
        orientation=orientation,
        age=age,
        country=country,
        state=state,
        city=city,
        zone=zone,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )

    return item.to_dict()


def extract_lat_lon_via_click(page):
    try:
        page.wait_for_selector('button.btn.btn-primary.mb-2', state='visible', timeout=10000)

        with page.expect_popup(timeout=15000) as popup_info:
            page.click('button.btn.btn-primary.mb-2', force=True)

        popup = popup_info.value
        url = popup.url
        logger.info(f"Popup URL captured: {url}")
        popup.close()

        match = re.search(r'daddr=([-\d\.]+),([-\d\.]+)', url)
        if match:
            lat, lon = match.group(1), match.group(2)
            return lat, lon

    except Exception as e:
        logger.warning(f"Could not extract lat/lon via click (popup): {e}")
        return None, None


def safe_int(value, default=0):
    try:
        if value is None or value == '' or value == 'null':
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def extract_data(soup):
    links = soup.find_all('a', href=True)

    results = []
    property_links = set()

    for link in links:
        href = link['href']
        if href.startswith('/propiedad/') and href not in property_links:
            property_links.add(href)

    for href in property_links:
        try:
            url = f'{config["BASE_URL"]}{href}'
            soup, page = get_child_item_data(href)
            item = parse_item(url, soup, page)
            results.append(item)
        except Exception as e:
            logger.error(e)

    return pd.DataFrame(results)


def get_child_item_data(url):
    new_page_link_item = config["BASE_URL"] + url
    page_item, soup_item = open_new_page(new_page_link_item, 'div.card-body')
    time.sleep(1)
    return soup_item, page_item


def open_new_page(page_link, selector_to_wait):
    global context
    page = context.new_page()

    page.set_extra_http_headers(config["HEADERS"])

    logger.info(page_link)

    try:
        page.goto(page_link)
    except:
        page.goto(page_link)

    page.wait_for_selector(selector_to_wait, timeout=30000)
    html = page.content()
    soup = BeautifulSoup(html, 'lxml')
    return page, soup


def run():
    global context
    global config

    config = load_config("scraper/configs/century21-config.json")
    scraper_service = ScraperService()

    with sync_playwright() as p:
        all_properties = []
        for current_page in tqdm(range(START_PAGE, START_PAGE + MAX_PAGES), desc="Scraping Century21"):
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=config["HEADERS"]["user-agent"])

            page_link = f'{config["BASE_URL"]}{config["LISTING_URL"].format(current_page)}'
            time.sleep(1)
            page, soup = open_new_page(page_link, 'a[href^="/propiedad/"]')

            properties = extract_data(soup)
            all_properties.extend(properties.to_dict('records'))

            browser.close()
            time.sleep(3)

        property_objects = [Property.from_dict(prop) for prop in all_properties]

        scraper_service.process_scraped_items(property_objects)


if __name__ == "__main__":
    run()
