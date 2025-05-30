from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from utils.property import Property
from utils.constants import Constants
from utils.configloader import load_config
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.dataformatter import DataFormatter
import re
import logging
from datetime import datetime, timezone
from services.scraper_service import ScraperService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Global constants
START_PAGE = 1
MAX_PAGES = 1
RETRIES = 3

context = None
config = None
global_zone_state = ""


def extract_property_id(url: str) -> str:
    """
    Extrae el ID de la propiedad de la URL de Zonaprop.
    Ejemplo: de /propiedades/clasificado/veclocin-oficina-usd1600-m-sup2--con-renta-del-4-anual-frente-56043402.html extrae 56043402
    """
    match = re.search(r'-(\d+)\.html$', url)
    return match.group(1) if match else ''


def extract_amenities(soup):
    """
    Extrae amenities del HTML de una propiedad de Zonaprop usando regex específicos por amenity.
    """
    found = []
    elements = soup.find_all(['li', 'span', 'div'])

    if not elements:
        return found

    text_elements = [el.get_text(strip=True).lower() for el in elements if el.get_text(strip=True)]

    for amenity, patterns in Constants.AMENITY_PATTERNS.items():
        for text in text_elements:
            if any(re.search(pat, text) for pat in patterns):
                found.append(amenity)
                break  # evita duplicados

    return list(set(found))


def parse_item(url, div):
    """
    Extrae los datos clave de la ficha de un inmueble en Zonaprop.
    """
    # Identification of the property
    property_id = extract_property_id(url)
    source_name = "zonaprop"
    source_identifier = f"{source_name}-{property_id}" if property_id else None
    scrape_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    container = div.select('.clearfix')
    price_dirty = extract_text_and_remove(container[2].select_one('.price-value').text.strip(), 'USD')
    price_currency, price = DataFormatter.clean_price_and_currency(price_dirty)
    expenses_element = container[2].select_one('.price-expenses')
    if expenses_element is None:
        expenses_currency = None
        expenses = 0
    else:
        expenses_currency, expenses = DataFormatter.clean_price_and_currency(
            extract_currency_amount(expenses_element.text.strip()))

    full_location = container[2].select_one('.section-location-property').text.strip()
    parts = full_location.split(',', 1)

    # Extract zone and address
    address = parts[0].strip() if parts else None
    location_parts = parts[1].strip().split(',') if len(parts) > 1 else []

    # Default values for Argentina
    country = "Argentina"
    state = global_zone_state
    city = location_parts[-1].strip() if len(location_parts) >= 1 else None
    zone = location_parts[-2].strip() if len(location_parts) >= 2 else None

    features = div.select('.section-icon-features-property>li')

    feature_data = extract_feature_data(features)

    total_surface = feature_data.get(Constants.TOTAL_SURFACE)

    sqr_price = price / total_surface if total_surface else 0
    sqr_price = round(sqr_price, 2)

    covered_surface = feature_data.get(Constants.COVERED_SURFACE) if feature_data.get(
        Constants.COVERED_SURFACE) else feature_data.get(Constants.TOTAL_SURFACE)
    rooms = feature_data.get(Constants.ROOMS) if feature_data.get(Constants.ROOMS) is not None else 0
    bedrooms = feature_data.get(Constants.BEDROOMS) if feature_data.get(Constants.BEDROOMS) is not None else 0
    bathrooms = feature_data.get(Constants.BATHROOMS) if feature_data.get(Constants.BATHROOMS) is not None else 0
    garages = feature_data.get(Constants.GARAGES) if feature_data.get(Constants.GARAGES) is not None else 0

    # Get latitude and longitude from the div object (added by get_child_item_data)
    latitude = getattr(div, 'latitude', None)
    longitude = getattr(div, 'longitude', None)
    location = f'POINT({longitude} {latitude})' if latitude and longitude else None

    orientation = feature_data.get(Constants.ORIENTATION)
    if orientation:
        orientation = orientation.lower()
        orientation = Constants.ORIENTATION_MAPPING.get(orientation, orientation)

    layout = feature_data.get(Constants.LAYOUT)
    if layout:
        layout = layout.lower()
        layout = Constants.LAYOUT_MAPPING.get(layout, layout)

    # Extract amenities
    amenities = extract_amenities(div)

    # Create Property object with organized fields
    item = Property(
        url=config["BASE_URL"] + url,
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
        amenities=amenities,
        age=DataFormatter.clean_age_data(feature_data.get(Constants.AGE)),
        layout=layout,
        orientation=orientation,
        country=country,
        state=state,
        city=city,
        zone=zone,
        address=address,
        latitude=latitude,
        longitude=longitude,
        location=location,
        is_active=True
    )
    return item.to_dict()


def extract_feature_data(features):
    extracted_data = {}
    for feature in features:
        value = feature.get_text()
        icon_class = feature.select_one('i')['class'][0]
        if icon_class in Constants.ZONAPROP_FEATURE_MAPPING:
            extracted_data[Constants.ZONAPROP_FEATURE_MAPPING[icon_class]] = extract_numbers(
                DataFormatter.clean_data(value))
    return extracted_data


def extract_text_and_remove(text, text_to_remove):
    parts = [part.strip() for part in text.split('\n') if part.strip() and text_to_remove in part]
    return parts[0] if parts else text


def extract_numbers(text):
    if text is None:
        return None
    match = re.search(r'\d+', text)
    return int(match.group()) if match else text


def extract_currency_amount(text):
    currency_amounts = re.findall(r'\$\s*\d+(?:\.\d+)?', text)
    return currency_amounts[0] if currency_amounts else None


def extract_coordinates_from_map(soup):
    """Extract latitude and longitude from the static map container."""
    map_container = soup.select_one('.static-map-container img#static-map')
    if map_container and 'src' in map_container.attrs:
        src = map_container['src']
        markers_match = re.search(r'markers=([-\d.]+),([-\d.]+)', src)
        if markers_match:
            return float(markers_match.group(1)), float(markers_match.group(2))
    return None, None


def extract_data(soup, page, page_link):
    container_div = soup.find('div', class_='postingsList-module__postings-container')

    for _ in range(RETRIES):
        if container_div:
            break
        logger.warning("No postings-container found in the page. Retrying...")
        time.sleep(5)
        page.goto(page_link)
        soup = BeautifulSoup(page.content(), 'lxml')
        container_div = soup.find('div', class_='postingsList-module__postings-container')

    if not container_div:
        logger.warning("Failed to find postings-container after retries.")
        return []

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
                    logger.info(url)
                    item_dict = parse_item(url, item_container)
                    prop = Property.from_dict(item_dict)
                    results.append(prop)
            except Exception as e:
                logger.error(e)

    return results


async def get_child_item_data(url):
    config = load_config("scraper/configs/zonaprop-config.json")
    new_page_link_item = config["BASE_URL"] + url

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=config["HEADERS"]["user-agent"])

        page = await context.new_page()
        await page.set_extra_http_headers(config["HEADERS"])

        try:
            await page.goto(new_page_link_item)
            await page.wait_for_selector('body#PROPERTY', timeout=30000)
            time.sleep(1)
            html_content = await page.content()
            soup_item = BeautifulSoup(html_content, 'lxml')

            container_div_item = soup_item.find('div', class_='main-container-property')

            # Extract coordinates from the map
            latitude, longitude = extract_coordinates_from_map(soup_item)
            if container_div_item is not None:
                container_div_item.latitude = latitude
                container_div_item.longitude = longitude

        except Exception as e:
            logger.error(f"Failed to load {new_page_link_item}: {e}")
        finally:
            await browser.close()

        return container_div_item


def open_new_page(page_link):
    global context
    page = context.new_page()

    page.set_extra_http_headers(config["HEADERS"])

    logger.info(f"Opening {page_link}")
    try:
        page.goto(page_link)
        page.wait_for_selector(".postingsList-module__postings-container", timeout=30000)
    except Exception as e:
        logger.warning(f"No main container found: {e}")
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
    global global_zone_state

    config = load_config("scraper/configs/zonaprop-config.json")
    scraper_service = ScraperService()

    with sync_playwright() as p:
        for zone in config["ZONES"]:
            logger.info(f"Starting scraping for zone: {zone['slug']}")
            for current_page in tqdm(range(START_PAGE, START_PAGE + MAX_PAGES),
                                     desc=f"Scraping ZonaProp - {zone['slug']}"):
                try:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent=config["HEADERS"]["user-agent"])

                    page_link = f'{config["BASE_URL"]}{config["LISTING_URL"]}{zone["slug"]}-pagina-{current_page}.html'
                    time.sleep(1)
                    page, soup = open_new_page(page_link)

                    global_zone_state = zone["state"]
                    properties = extract_data(soup, page, page_link)

                    if properties:
                        scraper_service.process_scraped_items(properties)
                        logger.info(f"✅ Zone {zone['slug']}, Page {current_page}: {len(properties)} properties saved.")
                    else:
                        logger.warning(f"⚠️ Zone {zone['slug']}, Page {current_page}: no properties found.")

                    browser.close()
                    time.sleep(3)

                except Exception as e:
                    logger.error(f"❌ Error processing zone {zone['slug']}, page {current_page}: {e}")
                    try:
                        browser.close()
                    except:
                        pass
                    continue

    scraper_service.close()
