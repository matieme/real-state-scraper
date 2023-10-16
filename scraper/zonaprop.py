from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time

# Global constants
START_PAGE = 2
MAX_PAGES = 10
RETRIES = 3
BASE_URL = "www.zonaprop.com.ar"

HEADERS = {
    'authority': 'www.zonaprop.com.ar',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9,es-US;q=0.8,es;q=0.7',
    'cache-control': 'max-age=0',
    'cookie': '_gcl_au=1.1.915058023.1696996656; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22jlgty5cYVRTfRmf7QASw%22%7D; sessionId=719d2a39-3b0c-4003-8780-fd99339b799b; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%7D; _fbp=fb.2.1696996656597.2087731844; _hjSessionUser_194887=eyJpZCI6ImM4ODc0NjhlLTdmNmQtNTE0Yi1iNmU4LWQzYTYyMWJiYzlkOCIsImNyZWF0ZWQiOjE2OTY5OTY2NTY4MTMsImV4aXN0aW5nIjp0cnVlfQ==; __cf_bm=OZ6ufJsMkxkuMAFLlrE9oT02YtKcNxABcP6HOxPrmgg-1697238054-0-ATedCiDMGh6TmhS5NkEoHwx+r27IOrLp0d1rOsHrPTsqQLAiApgVn8CJZTDeur2GVNa9dXiOjfE/q8P4j088l1Wy7Gsc/r1yfqn1PV0J9ERw; cf_clearance=mjz7bP3BLQtHQkKVc9iugIGzRstWW_U2scjf4zvc5lI-1697238064-0-1-27c0c582.189fedc2.39a8e4c8-160.2.1697238064; _gid=GA1.3.864520911.1697238062; __gads=ID=ee8269041c5e1324:T=1696996656:RT=1697238064:S=ALNI_MZb-zqUx8CHbjVpcEZg2AU8mPWB5Q; __gpi=UID=00000a17b9f09a29:T=1696996656:RT=1697238064:S=ALNI_MZL2WqEfjo5_Gir3Mtb2pe5R20Ntw; JSESSIONID=9A28797E85CEF81B28FB25A2CA17E39A; _ga_68T3PL08E4=GS1.1.1697238063.6.0.1697238063.60.0.0; _ga=GA1.1.392380778.1696996656; _hjIncludedInSessionSample_194887=0; _hjSession_194887=eyJpZCI6IjEyNTFkMWY1LWNhNTUtNGJjYS05MTJjLWIyMTFhMDFlYTg2NCIsImNyZWF0ZWQiOjE2OTcyMzgwNjMxOTAsImluU2FtcGxlIjpmYWxzZSwic2Vzc2lvbml6ZXJCZXRhRW5hYmxlZCI6ZmFsc2V9; _hjAbsoluteSessionInProgress=1',
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

context = None


def parse_item(div):
    href = div.find('div', attrs={'data-qa': 'posting PROPERTY'}).get("data-to-posting")

    # Extracting price
    price = div.find('div', attrs={'data-qa': 'POSTING_CARD_PRICE'}).text

    # Extracting location
    location = div.find('div', attrs={'data-qa': 'POSTING_CARD_LOCATION'}).text

    # Extracting features
    features_element = div.find('div', attrs={'data-qa': 'POSTING_CARD_FEATURES'})
    features = [x.text for x in features_element.find_all('span') if x.find("img")]
    total_surface = features[0] if len(features) > 0 and features[0] else None
    covered_surface = features[1] if len(features) > 1 and features[1] else None
    rooms = features[2] if len(features) > 2 and features[2] else None
    bedrooms = features[3] if len(features) > 3 and features[3] else None
    bathrooms = features[4] if len(features) > 4 and features[4] else None
    garages = features[5] if len(features) > 5 and features[5] else None

    item = {
        "Referencia": href,
        "Price": price,
        "Location": location,
        "Total Surface": total_surface,
        "Covered Surface": covered_surface,
        "Rooms": rooms,
        "Bedrooms": bedrooms,
        "Bathrooms": bathrooms,
        "Garages": garages
    }

    return item


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
    for i, div in enumerate(container_div.contents):
        try:
            if div:
                item = parse_item(div)
                # print(item)
                results.append(item)
        except Exception as e:
            print(e)
            pass

    return pd.DataFrame(results)


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

            page_link = f'https://www.zonaprop.com.ar/casas-venta-capital-federal-pagina-{current_page}.html'
            page, soup = open_new_page(page_link)
            df_page = extract_data(soup, page, page_link)

            df_page.to_csv(f"results/scraped_zonaprop_page_{current_page}.csv", index=False)

            browser.close()  # Close browser after processing each page

            time.sleep(2)  # Add a delay after closing the browser before opening a new one for the next URL
