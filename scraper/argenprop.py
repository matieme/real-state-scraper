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
MAX_PAGES = 3
RETRIES = 3

context = None
config = None
global_zone_state = ""


def extract_property_id(url: str) -> str:
    """
    Extrae el ID de la propiedad de la URL de Argenprop.
    Ejemplo: de /departamento-en-venta-en-recoleta-4-ambientes--17014913 extrae 17014913
    """
    match = re.search(r'--(\d+)$', url)
    return match.group(1) if match else ''


def extract_amenities(soup):
    """
    Extrae las amenities del inmueble en Argenprop desde div.property-description,
    recorriendo todos los <li class="property-features-item"> encontrados dentro de secciones.
    """
    found_amenities = []
    description_container = soup.select_one('div.property-description')

    if not description_container:
        return found_amenities

    items = description_container.select('li.property-features-item')

    for item in items:
        text = item.get_text(strip=True).lower()
        for amenity, patterns in Constants.AMENITY_PATTERNS.items():
            if any(re.search(pattern, text) for pattern in patterns):
                found_amenities.append(amenity)
                break

    return list(set(found_amenities))


def parse_item(url, soup):
    # Extraer ID de la propiedad
    property_id = extract_property_id(url)
    source_name = "argenprop"
    source_identifier = f"{source_name}-{property_id}" if property_id else None
    scrape_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1) selecciono el bloque principal
    main_div = soup.select_one('div.property-main')

    # 2) precio y moneda
    raw_price = main_div.select_one('p.titlebar__price').get_text(strip=True)
    price_currency = "USD" if raw_price.upper().startswith("USD") else "ARS"
    price = DataFormatter.extract_int_value(raw_price)

    # 3) expensas (opcional)
    exp_elem = main_div.select_one('p.titlebar__expenses')
    expenses = DataFormatter.extract_int_value(exp_elem.get_text()) if exp_elem else 0

    # 4) dirección exacta
    address = (
        main_div.select_one('h2.titlebar__address')
        .get_text(strip=True)
    )

    # 5) barrio / localidad
    loc_text = main_div.select_one('h2.titlebar__title').get_text(strip=True)
    loc_text = re.sub(r'(?i)^venta en ', '', loc_text)
    zone = loc_text.split(',')[0].strip()

    # Default values for Argentina
    country = "Argentina"
    state = global_zone_state
    city = loc_text.split(',')[1].strip()

    # 6) features (rooms, baños, superficie…)
    features = main_div.select('ul.property-main-features > li')
    complete_data = extract_feature_data(features)

    total_surface = complete_data.get(Constants.TOTAL_SURFACE,
                                      complete_data.get(Constants.COVERED_SURFACE, 0))
    covered_surface = complete_data.get(Constants.COVERED_SURFACE, total_surface)
    sqr_price = round(price / total_surface, 2) if total_surface else 0
    rooms = clean_rooms_data(complete_data.get(Constants.ROOMS))
    bedrooms = complete_data.get(Constants.BEDROOMS, 0)
    bathrooms = complete_data.get(Constants.BATHROOMS, 0)
    garages = complete_data.get(Constants.GARAGES, 0)
    age = DataFormatter.clean_age_data(complete_data.get(Constants.AGE))
    layout = clean_repeated_words(complete_data.get(Constants.LAYOUT))
    if layout:
        layout = layout.lower()
        layout = Constants.LAYOUT_MAPPING.get(layout, layout)
    orientation = clean_repeated_words(complete_data.get(Constants.ORIENTATION))
    if orientation:
        orientation = orientation.lower()
        orientation = Constants.ORIENTATION_MAPPING.get(orientation, orientation)

    # 7) coordenadas
    leaflet = soup.find('div', attrs={'data-latitude': True, 'data-longitude': True})

    if leaflet:
        raw_lat = leaflet.get('data-latitude', '')
        raw_lon = leaflet.get('data-longitude', '')
        latitude = raw_lat.replace(',', '.')
        longitude = raw_lon.replace(',', '.')
        location = f'POINT({longitude} {latitude})'
    else:
        latitude = longitude = location = None

    # Extract amenities
    amenities = extract_amenities(soup)

    # 8) armo el dict con tu clase
    item = Property(
        url=config["BASE_URL"] + url,
        source_name=source_name,
        source_identifier=source_identifier,
        scrape_date=scrape_date,
        price_currency=price_currency,
        price=price,
        expenses_currency='ARS',
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
                item_dict = parse_item(url, get_child_item_data(url))
                prop = Property.from_dict(item_dict)
                results.append(prop)
        except Exception as e:
            logger.error(e)
            pass

    return results


def get_child_item_data(url):
    new_page_link_item = config["BASE_URL"] + url
    page_item, soup_item = open_new_page(new_page_link_item)
    time.sleep(1)
    # container_div_item = soup_item.find('div', class_='property-main')
    return soup_item


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

    logger.info(f"Opening {page_link}")
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
    global global_zone_state

    config = load_config("scraper/configs/argenprop-config.json")
    scraper_service = ScraperService()

    with sync_playwright() as p:
        for zone in config["ZONES"]:
            logger.info(f"Starting scraping for zone: {zone['slug']}")
            for current_page in tqdm(range(START_PAGE, START_PAGE + MAX_PAGES),
                                     desc=f"Scraping Argenprop - {zone['slug']}"):
                try:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent=config["HEADERS"]["user-agent"])

                    page_link = f'{config["BASE_URL"]}{config["LISTING_URL"]}{zone["slug"]}/pagina-{current_page}'
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
