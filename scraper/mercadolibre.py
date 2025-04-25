from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse
from tqdm import tqdm
import logging

from utils.property import Property
from utils.constants import Constants
from utils.configloader import load_config
from utils.dataformatter import DataFormatter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

START_PAGE = 1
MAX_PAGES = 10
RETRIES = 3
RESULTS_PER_PAGE = 48

config = None


def build_page_url(page_number: int) -> str:
    """
    Construye la URL de la página de resultados para MercadoLibre.
    """
    if page_number == 1:
        return config["BASE_URL"] + "/"
    offset = 1 + (page_number - 1) * RESULTS_PER_PAGE
    return f"{config['BASE_URL']}/_Desde_{offset}_NoIndex_True"


def open_new_page(page, url: str) -> BeautifulSoup:
    """
    Abre una URL en Playwright y retorna el Soup.
    """
    logger.info(f"Abriendo {url}")
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


def parse_item_ml(url: str, soup: BeautifulSoup) -> dict:
    """
    Extrae los datos clave de la ficha de un inmueble en MercadoLibre.
    """
    # Precio y moneda
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
    exact_direction = ''
    location = ''
    
    if location_container:
        # Obtener la dirección completa
        address = location_container.select_one('p.ui-pdp-color--BLACK.ui-pdp-size--SMALL')
        if address:
            full_address = address.get_text(strip=True).lower()
            # Obtener solo la parte antes de la primera coma
            exact_direction = full_address.split(',')[0].strip()
            # El resto de la dirección (después de la primera coma) se usa para la ubicación
            location_parts = full_address.split(',')[1:]
            if location_parts:
                location = ','.join(location_parts).strip()

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
    age = specs.get('Antigüedad', None)
    layout = specs.get('Disposición', None)
    orientation = specs.get('Orientación', None)
    
    # Expensas
    expenses_str = specs.get('Expensas', '0 ARS')
    expenses = DataFormatter.extract_int_value(expenses_str)
    expenses_currency = 'ARS'

    # Coordenadas desde el mapa estático
    latitude = longitude = None
    map_img = soup.select_one('img.ui-pdp-image[src*="staticmap"]')
    if map_img:
        src = map_img['src']
        params = urllib.parse.parse_qs(urllib.parse.urlparse(src).query)
        center = params.get('center', [''])[0]
        if center:
            latitude, longitude = center.split(',')

    item = Property(
        url=url,
        reference='mercadolibre',
        price_currency=price_currency,
        price=price,
        expenses_currency=expenses_currency,
        expenses=expenses,
        sqr_price=sqr_price,
        location=location,
        exact_direction=exact_direction,
        total_surface=total_surface,
        covered_surface=covered_surface,
        rooms=rooms,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        garages=garages,
        age=age,
        layout=layout,
        orientation=orientation,
        latitude=latitude,
        longitude=longitude,
    )
    return item.to_dict()


def extract_data_ml(soup: BeautifulSoup, page, page_link: str) -> pd.DataFrame:
    """
    Extrae el listado de enlaces y realiza parse_item_ml en cada ficha.
    """
    container = soup.find('ol', class_='ui-search-layout')
    if not container:
        logger.warning("No se encontró el listado de inmuebles.")
        return pd.DataFrame()

    results = []
    for tag in container.find_all('li', recursive=False):
        try:
            link = tag.find('a', href=True)['href']
            child_soup = open_new_page(page, link)
            time.sleep(1)
            item = parse_item_ml(link, child_soup)
            results.append(item)
        except Exception as e:
            logger.error(e)
    return pd.DataFrame(results)


def run():
    global config
    config = load_config("scraper/configs/mercadolibre-config.json")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=config["HEADERS"]["user-agent"])
        page = context.new_page()
        page.set_extra_http_headers(config["HEADERS"])

        for current_page in tqdm(range(START_PAGE, MAX_PAGES + 1)):
            page_url = build_page_url(current_page)
            soup = open_new_page(page, page_url)
            df = extract_data_ml(soup, page, page_url)
            df.to_csv(f"results/scraped_ml_page_{current_page}.csv", index=False)
            time.sleep(2)

        browser.close()