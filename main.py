import logging
import time
from scraper import zonaprop, argenprop, mercadolibre, century_21

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def run_scraper():
    zonaprop.run()
    mercadolibre.run()
    argenprop.run()
    century_21.run()


def main():
    logger.info(f"Starting main script at {time.strftime('%H:%M:%S')}")
    run_scraper()
    logger.info("Finished all tasks.")


if __name__ == "__main__":
    main()
