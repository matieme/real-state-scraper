﻿import logging
import time
from scraper import zonaprop, argenprop, mercadolibre
from utils import filemerger

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def run_scraper():
    logger.info("Starting the zonaprop scraper...")
    zonaprop.run()
    logger.info("Finished the zonaprop scraper.")
    logger.info("Starting the Mercado Libre scraper...")
    mercadolibre.run()
    logger.info("Finished the Mercado Libre scraper.")
    logger.info("Starting the argenprop scraper...")
    argenprop.run()
    logger.info("Finished the zonaprop scraper.")
    logger.info("Merging the results...")
    filemerger.merge_files()


def main():
    logger.info(f"Starting main script at {time.strftime('%H:%M:%S')}")
    run_scraper()
    logger.info("Finished all tasks.")


if __name__ == "__main__":
    main()
