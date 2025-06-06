from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
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
MAX_PAGES = 3
RETRIES = 3

context = None
config = None
global_zone_state = ""


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
        return 1


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


def extract_amenities(soup):
    """
    Extrae amenities del inmueble en Century21 comparando el texto de cada div dentro de
    'card-body pt-0' contra los patrones de AMENITY_PATTERNS.
    """
    found_amenities = []
    container = soup.select_one('div.card-body.pt-0')

    if not container:
        return found_amenities

    inner_divs = container.find_all('div')

    for div in inner_divs:
        text = div.get_text(strip=True).lower()

        for amenity, patterns in Constants.AMENITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    found_amenities.append(amenity)
                    break

    return list(set(found_amenities))


def extract_surface_value(data_str: str) -> int:
    """
    Extrae la parte entera de un número en formato '118.590000' -> 118.
    Se usa para datos de Century21 donde el valor decimal no representa centavos.

    Args:
        data_str (str): String con el número (con punto como decimal visual).

    Returns:
        int: Parte entera como número.
    """
    try:
        integer_part = str(data_str).split('.')[0]
        return int(integer_part)
    except (ValueError, AttributeError):
        return 0


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

    # Extract address and zone
    full_direction = get_meta_content('direccion').strip()
    parts = full_direction.split(',', 1)
    location_parts = parts[1].strip().split(',') if len(parts) > 1 else []
    address = parts[0].strip() if parts else None

    country = "Argentina"
    state = global_zone_state
    city = location_parts[-2].strip() if len(location_parts) >= 2 else None
    zone = get_meta_content('municipio')

    total_surface = extract_surface_value(get_meta_content('MT'))
    covered_surface = extract_surface_value(get_meta_content('MC'))
    if total_surface == 0 and covered_surface > 0:
        total_surface = covered_surface

    rooms = extract_rooms_from_icons(soup)
    bedrooms = safe_int(get_meta_content('recamaras') or 1)
    bathrooms = safe_int(get_meta_content('banio') or 0)
    garages = safe_int(get_meta_content('estacionamiento') or 0)
    sqr_price = round(price / total_surface, 2) if price and total_surface else 0

    age = extract_age_from_icons(soup)

    latitude, longitude = extract_lat_lon_via_click(page)
    location = f'POINT({longitude} {latitude})' if latitude and longitude else None

    layout = None
    if layout:
        layout = layout.lower()
        layout = Constants.LAYOUT_MAPPING.get(layout, layout)
    orientation = None
    if orientation:
        orientation = orientation.lower()
        orientation = Constants.ORIENTATION_MAPPING.get(orientation, orientation)

    # Extract amenities
    amenities = extract_amenities(soup)

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
        location=location,
        amenities=amenities,
        is_active=True
    )

    return item.to_dict()


def extract_lat_lon_via_click(page):
    try:
        page.wait_for_selector('button.btn.btn-primary.mb-2', state='visible', timeout=10000)

        with page.expect_popup(timeout=15000) as popup_info:
            page.click('button.btn.btn-primary.mb-2', force=True)

        popup = popup_info.value
        url = popup.url
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
        url = f'{config["BASE_URL"]}{href}'
        try:
            soup, page = get_child_item_data(href)
            item_dict = parse_item(url, soup, page)
            prop = Property.from_dict(item_dict)
            results.append(prop)
            logger.info(f"Save property: {config['BASE_URL'] + url}")
        except Exception as e:
            logger.error(f"Error parsing item at {config['BASE_URL'] + url}: {e}")

    return results


def get_child_item_data(url):
    new_page_link_item = config["BASE_URL"] + url
    page_item, soup_item = open_new_page(new_page_link_item, 'div.card-body')
    time.sleep(1)
    return soup_item, page_item


def open_new_page(page_link, selector_to_wait):
    global context
    page = context.new_page()

    page.set_extra_http_headers(config["HEADERS"])

    logger.info("")
    logger.info(f"Opening page: {page_link}")
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
    global global_zone_state

    logger.info("==== Century21 Scraper Started ====")
    config = load_config("scraper/configs/century21-config.json")
    scraper_service = ScraperService()

    with sync_playwright() as p:
        for zone in config["ZONES"]:
            logger.info(f"Starting scraping for zone: {zone['slug']}")
            for current_page in tqdm(range(START_PAGE, START_PAGE + MAX_PAGES),
                                     desc=f"Scraping Century21 - {zone['slug']}"):
                page_link = f'{config["BASE_URL"]}{config["LISTING_URL"].format(current_page)}{zone["slug"]}'
                time.sleep(1)
                try:
                    with p.chromium.launch(headless=True) as browser:
                        with browser.new_context(user_agent=config["HEADERS"]["user-agent"]) as context:
                            page, soup = open_new_page(page_link, 'a[href^="/propiedad/"]')
                            global_zone_state = zone['state']

                            properties = extract_data(soup)

                            if properties:
                                scraper_service.process_scraped_items(properties)
                                logger.info(
                                    f"✅ Zone {zone['slug']}, Page {current_page}: {len(properties)} properties saved successfully.")
                            else:
                                logger.warning(
                                    f"⚠️ Zone {zone['slug']}, Page {current_page}: no properties found.")
                            time.sleep(3)

                except Exception as e:
                    logger.error(
                        f"❌ Error processing zone {zone['slug']}, page {current_page}: {e}")
                    continue

    scraper_service.close()
    logger.info("==== Century21 Scraper Finished ====")
