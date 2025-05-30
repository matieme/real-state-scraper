from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse
from tqdm import tqdm
import logging
from datetime import datetime, timezone

from utils.property import Property
from utils.constants import Constants
from utils.configloader import load_config
from utils.dataformatter import DataFormatter
from services.scraper_service import ScraperService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

START_PAGE = 1
MAX_PAGES = 1
RETRIES = 3
RESULTS_PER_PAGE = 48

config = None
global_zone_state = ""


def build_page_url(page_number: int, zone_slug: str) -> str:
    """
    Construye la URL de la página de resultados para MercadoLibre.
    """
    if page_number == 1:
        return f"{config['BASE_URL']}{config['LISTING_URL']}{zone_slug}/"
    offset = 1 + (page_number - 1) * RESULTS_PER_PAGE
    return f"{config['BASE_URL']}{config['LISTING_URL']}{zone_slug}/_Desde_{offset}_NoIndex_True"


def open_new_page(page, url: str) -> BeautifulSoup:
    """
    Abre una URL en Playwright y retorna el Soup.
    """
    logger.info(f"Opening page: {url}")
    try:
        page.goto(url)
    except Exception:
        page.goto(url)
    html = page.content()
    return BeautifulSoup(html, 'lxml')


def extract_specs_from_table(soup):
    """
    Extrae las especificaciones de la tabla 'Principales' del inmueble.
    """
    specs = {}
    specs_table = soup.select_one('div.ui-vpp-striped-specs__table')
    if not specs_table:
        return specs

    for row in specs_table.select('tr.andes-table__row'):
        header = row.select_one('div.andes-table__header__container')
        value = row.select_one('span.andes-table__column--value')

        if header and value:
            key = header.get_text(strip=True)
            val = value.get_text(strip=True)
            specs[key] = val

    return specs


def extract_property_id(url: str) -> str:
    """
    Extrae el ID de la propiedad de la URL de MercadoLibre.
    Ejemplo: de https://casa.mercadolibre.com.ar/MLA-1464845225-casa... extrae MLA-1464845225
    """
    match = re.search(r'/(MLA-\d+)-', url)
    return match.group(1) if match else ''


def extract_amenities(soup):
    """
    Extrae amenities del HTML de MercadoLibre recorriendo todas las tablas dentro del bloque
    ui-vpp-striped-specs, y chequeando que el valor asociado al amenity sea "Sí".
    """
    found_amenities = []
    specs_containers = soup.select('div.ui-vpp-striped-specs')

    if not specs_containers:
        return found_amenities

    for container in specs_containers:
        tables = container.select('div.ui-vpp-striped-specs__table')

        for table in tables:
            table_body = table.select_one('tbody.andes-table__body')
            if not table_body:
                continue

            rows = table_body.select('tr.andes-table__row')
            for row in rows:
                th = row.find('th')
                td = row.find('td')

                if not th or not td:
                    continue

                label = th.get_text(strip=True).lower()
                value = td.get_text(strip=True).lower()

                if value in ['sí', 'si']:
                    for amenity, patterns in Constants.AMENITY_PATTERNS.items():
                        if any(re.search(pattern, label) for pattern in patterns):
                            found_amenities.append(amenity)
                            break

    return list(set(found_amenities))


def parse_item_ml(url: str, soup: BeautifulSoup) -> dict:
    """
    Extrae los datos clave de la ficha de un inmueble en MercadoLibre.
    """
    # Identification of the property
    property_id = extract_property_id(url)
    source_name = "mercadolibre"
    source_identifier = f"{source_name}-{property_id}" if property_id else None
    scrape_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Offer of the property
    price_container = soup.select_one('span.andes-money-amount')
    price = 0
    price_currency = None

    if price_container:
        # Obtener precio del meta tag dentro del contenedor
        price_meta = price_container.select_one('meta[itemprop="price"]')
        if price_meta:
            price = int(float(price_meta['content']))

        # Obtener moneda y convertir US$ a USD
        currency_symbol = price_container.select_one('span.andes-money-amount__currency-symbol')
        if currency_symbol:
            currency = currency_symbol.get_text(strip=True)
            price_currency = 'USD' if currency == 'US$' else currency

    # Ubicación y dirección exacta
    location_container = soup.select_one('div.ui-vip-location')
    address = ''
    zone = ''

    if location_container:
        # Obtener la dirección completa
        address_elem = location_container.select_one('p.ui-pdp-color--BLACK.ui-pdp-size--SMALL')
        if address_elem:
            full_address = address_elem.get_text(strip=True)
            # Split by commas and clean up
            parts = [part.strip() for part in full_address.split(',')]

            # Default values for Argentina
            country = "Argentina"
            state = global_zone_state
            city = parts[-2].strip() if len(parts) >= 1 else None
            zone = parts[-3].strip() if len(parts) >= 2 else None

            # Extract address and zone
            if len(parts) >= 1:
                address = parts[0]

    # Extraer datos de la tabla de especificaciones
    specs = extract_specs_from_table(soup)

    # Superficies
    total_surface = DataFormatter.extract_int_value(specs.get('Superficie total', '0 m²'))
    covered_surface = DataFormatter.extract_int_value(specs.get('Superficie cubierta', str(total_surface) + ' m²'))

    # Calcular precio por metro cuadrado
    sqr_price = round(price / total_surface, 2) if total_surface else 0

    # Ambientes y características
    rooms = DataFormatter.extract_int_value(specs.get('Ambientes', '0'))
    bedrooms = DataFormatter.extract_int_value(specs.get('Dormitorios', '0'))
    bathrooms = DataFormatter.extract_int_value(specs.get('Baños', '0'))
    garages = DataFormatter.extract_int_value(specs.get('Cocheras', '0'))

    # Otros detalles
    age = DataFormatter.clean_age_data(specs.get('Antigüedad', None))
    layout = specs.get('Disposición', None)
    if layout:
        layout = layout.lower()
        layout = Constants.LAYOUT_MAPPING.get(layout, layout)
    orientation = specs.get('Orientación', None)
    if orientation:
        orientation = orientation.lower()
        orientation = Constants.ORIENTATION_MAPPING.get(orientation, orientation)

    # Expensas
    expenses_str = specs.get('Expensas', '0 ARS')
    expenses = DataFormatter.extract_int_value(expenses_str)
    expenses_currency = 'ARS'

    # Coordenadas desde el mapa estático
    latitude = longitude = location = None
    map_img = soup.select_one('img.ui-pdp-image[src*="staticmap"]')
    if map_img:
        src = map_img['src']
        params = urllib.parse.parse_qs(urllib.parse.urlparse(src).query)
        center = params.get('center', [''])[0]
        if center:
            latitude, longitude = center.split(',')
            location = f'POINT({longitude} {latitude})'

    # Extract amenities
    amenities = extract_amenities(soup)

    # Create Property object with organized fields
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
        amenities=amenities,
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
        is_active=True
    )
    return item.to_dict()


def extract_data_ml(soup: BeautifulSoup, page, page_link: str):
    """
    Extrae el listado de enlaces y realiza parse_item_ml en cada ficha.
    """
    container = soup.find('ol', class_='ui-search-layout')
    if not container:
        logger.warning(f"No property listing found on page {page_link}")
        return pd.DataFrame()

    results = []
    for tag in container.find_all('li', recursive=False):
        try:
            link = tag.find('a', href=True)['href']
            child_soup = open_new_page(page, link)
            time.sleep(2)
            item_dict = parse_item_ml(link, child_soup)
            prop = Property.from_dict(item_dict)
            results.append(prop)
            logger.info(f"Save property: {link}")
        except Exception as e:
            logger.error(f"Error parsing item at {link}: {e}")

    return results


def run():
    global config
    global global_zone_state

    logger.info("==== MercadoLibre Scraper Started ====")
    config = load_config("scraper/configs/mercadolibre-config.json")
    scraper_service = ScraperService()

    with sync_playwright() as p:
        for zone in config["ZONES"]:
            logger.info(f"Starting scraping for zone: {zone['slug']}")
            for current_page in tqdm(range(START_PAGE, START_PAGE + MAX_PAGES),
                                     desc=f"Scraping Mercado Libre - {zone['slug']}"):
                try:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent=config["HEADERS"]["user-agent"])
                    page = context.new_page()
                    page.set_extra_http_headers(config["HEADERS"])

                    page_url = build_page_url(current_page, zone["slug"])
                    soup = open_new_page(page, page_url)
                    global_zone_state = zone["state"]

                    properties = extract_data_ml(soup, page, page_url)

                    if properties:
                        scraper_service.process_scraped_items(properties)
                        logger.info(f"✅ Zone {zone['slug']}, Page {current_page}: {len(properties)} properties saved successfully.")
                    else:
                        logger.warning(f"⚠️ Zone {zone['slug']}, Page {current_page}: no properties found.")

                    time.sleep(2)

                except Exception as e:
                    logger.error(f"❌ Error processing zone {zone['slug']}, page {current_page}: {e}")
                    try:
                        browser.close()
                    except:
                        pass
                    continue

        browser.close()
        scraper_service.close()
        logger.info("==== MercadoLibre Scraper Finished ====")
