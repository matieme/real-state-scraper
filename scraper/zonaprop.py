from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from ipdb import set_trace
from bs4 import BeautifulSoup
import pandas as pd
import os
from tqdm import tqdm
import time
from utils import filemerger
from utils.property import Property


def parse_item(div):
    href = div.find('div', attrs={'data-qa': 'posting PROPERTY'}).get("data-to-posting")

    # Extracting price
    price = div.find('div', attrs={'data-qa': 'POSTING_CARD_PRICE'}).text
    price = price.split('USD ')[1]

    # Extracting location
    location = div.find('div', attrs={'data-qa': 'POSTING_CARD_LOCATION'}).text

    # Extracting features
    features_element = div.find('div', attrs={'data-qa': 'POSTING_CARD_FEATURES'})
    features = [x.text for x in features_element.find_all('span') if x.find("img")]
    total_surface = features[0]
    covered_surface = features[1]
    rooms = features[2]
    bedrooms = features[3]
    bathrooms = features[4]
    garages = features[5]

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
    # Find the first div with class="postings-container"
    container_div = soup.find('div', class_='postings-container')

    # Find all divs within the container div
    # divs = container_div.find_all('div')
    retries = 3  # Define the number of retries
    while container_div is None and retries > 0:
        print("No postings-container found in the page. Retrying...")
        time.sleep(5)  # Wait for 5 seconds

        # Reload the page
        page.goto(page_link)
        html = page.content()
        soup = BeautifulSoup(html, 'lxml')
        container_div = soup.find('div', class_='postings-container')

        retries -= 1  # Decrement the retry count

    if container_div is None:  # If still None after retries
        print("Failed to find postings-container after retries.")
        return pd.DataFrame()  # Return an empty DataFrame

    # List to store the extracted data
    results = []
    # Iterate over the divs and extract the relevant information
    for i, div in enumerate(container_div.contents):
        try:
            if div:
                item = parse_item(div)
                # print(item)
                results.append(item)
        except Exception as e:
            #print(e)
            pass

    return pd.DataFrame(results)


start_page = 2
max_pages = 3


def run():
    with sync_playwright() as p:
        for current_page in tqdm(range(start_page, max_pages + 1)):
            browser = p.chromium.launch(headless=False)  # Move browser initialization inside the loop

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            )

            page = context.new_page()

            headers = {
                'authority': 'www.zonaprop.com.ar',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9,es-US;q=0.8,es;q=0.7',
                'cache-control': 'max-age=0',
                'cookie': '_gcl_au=1.1.915058023.1696996656; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22jlgty5cYVRTfRmf7QASw%22%7D; _gid=GA1.3.909566837.1696996656; sessionId=719d2a39-3b0c-4003-8780-fd99339b799b; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%7D; _fbp=fb.2.1696996656597.2087731844; _hjSessionUser_194887=eyJpZCI6ImM4ODc0NjhlLTdmNmQtNTE0Yi1iNmU4LWQzYTYyMWJiYzlkOCIsImNyZWF0ZWQiOjE2OTY5OTY2NTY4MTMsImV4aXN0aW5nIjp0cnVlfQ==; __cf_bm=ZKDgzS1o3fx68DUge6PTgHPu7W42Z9NZzLZYCo9g_SA-1697064859-0-AbMXnhffFxiKcMKE6zQeZuA86b7uKrq7JujXDFrYGLBd9SODuOWmiQx2UCaN2QlwUMNETHmIJ1tZ1eX+fbT0Go60I5FMC5aLzOihKV/ED2mS; _dc_gtm_UA-5217585-1=1; cf_clearance=6NEqR9IScjs6l2qXwhqj7A_wuD6aRMQklUcebxGwg5Y-1697064860-0-1-5a96a806.f237fc96.d300f59c-160.2.1697064860; __gads=ID=ee8269041c5e1324:T=1696996656:RT=1697064860:S=ALNI_MZb-zqUx8CHbjVpcEZg2AU8mPWB5Q; __gpi=UID=00000a17b9f09a29:T=1696996656:RT=1697064860:S=ALNI_MZL2WqEfjo5_Gir3Mtb2pe5R20Ntw; _hjIncludedInSessionSample_194887=0; _hjSession_194887=eyJpZCI6ImQyMmUyMWE5LTZiYzUtNDhmMy1iNmFhLTg0OGVkODJmZGIwMiIsImNyZWF0ZWQiOjE2OTcwNjQ4NTg0NjcsImluU2FtcGxlIjpmYWxzZSwic2Vzc2lvbml6ZXJCZXRhRW5hYmxlZCI6ZmFsc2V9; _hjAbsoluteSessionInProgress=1; _ga=GA1.3.392380778.1696996656; _ga_68T3PL08E4=GS1.1.1697064858.3.0.1697064859.59.0.0; JSESSIONID=4B7A8D2F1B38493306CF41E2B3CE4342',
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

            page.set_extra_http_headers(headers)

            page_link = f'https://www.zonaprop.com.ar/casas-venta-capital-federal-pagina-{current_page}.html'
            print(page_link)
            try:
                page.goto(page_link)
            except:
                page.goto(page_link)

            html = page.content()
            soup = BeautifulSoup(html, 'lxml')
            df_page = extract_data(soup, page, page_link)

            df_page.to_csv(f"results/scraped_page_{current_page}.csv", index=False)

            browser.close()  # Close browser after processing each page

            time.sleep(2)  # Add a delay after closing the browser before opening a new one for the next URL

        filemerger.merge_files()
