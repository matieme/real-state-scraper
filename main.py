import logging
import time
from scraper import zonaprop, argenprop, mercadolibre, century_21

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def run_scraper():
    logger.info("Starting the Zonaprop scraper...")
    zonaprop.run()
    logger.info("Finished the Zonaprop scraper.")
    logger.info("Starting the Mercado Libre scraper...")
    mercadolibre.run()
    logger.info("Finished the Mercado Libre scraper.")
    logger.info("Starting the Argenprop scraper...")
    argenprop.run()
    logger.info("Finished the Argenprop scraper.")
    logger.info("Starting the Century 21 scraper...")
    century_21.run()
    logger.info("Finished the Century 21 scraper.")


def main():
    logger.info(f"Starting main script at {time.strftime('%H:%M:%S')}")
    run_scraper()
    logger.info("Finished all tasks.")


if __name__ == "__main__":
    main()
