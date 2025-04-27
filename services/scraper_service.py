import logging
from typing import List
from db.db_client import DBClient
from utils.property import Property
from utils.configloader import load_config

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        """Inicializa el servicio de scraping."""
        # Cargar configuración de la base de datos
        self.db_config = load_config("scraper/configs/database-config.json")
        self.db = DBClient(
            host=self.db_config["host"],
            database=self.db_config["database"],
            user=self.db_config["user"],
            password=self.db_config["password"],
            port=self.db_config.get("port", 5432)
        )

    def process_scraped_items(self, items: List[Property]):
        """
        Procesa los items scrapeados y los guarda en la base de datos.
        Args:
            items: Lista de objetos Property
        """
        try:
            logger.info(f"Processing {len(items)} scraped items")
            self.db.bulk_upsert_properties(items)
            logger.info("Successfully processed and saved all items")
        except Exception as e:
            logger.error(f"Error processing scraped items: {e}")
            raise
        finally:
            self.db.close()

    def process_single_item(self, item: Property):
        """
        Procesa un único item scrapeado y lo guarda en la base de datos.
        Args:
            item: Objeto Property
        """
        try:
            logger.info(f"Processing single item from {item.source_name}")
            self.db.upsert_property(item)
            logger.info("Successfully processed and saved item")
        except Exception as e:
            logger.error(f"Error processing single item: {e}")
            raise
