import logging
from typing import List
from db.db_client import DBClient
from utils.property import Property
import psycopg2
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        """Initializes the scraping service with a live DB connection."""
        load_dotenv()  # Load environment variables from .env file
        self.db = None
        self._connect_db()

    def _connect_db(self):
        """Creates a new DBClient connection."""
        self.db = DBClient(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_DATABASE'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', 5432))
        )

    def _ensure_connection(self):
        """Re-establishes DB connection if it was lost."""
        try:
            self.db.conn.cursor()
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            logger.warning("⚠️ Lost database connection. Reconnecting...")
            self._connect_db()

    def process_scraped_items(self, items: List[Property]):
        """Processes and stores a batch of scraped properties."""
        if not items:
            return

        logger.info(f"Processing {len(items)} items")

        try:
            self._ensure_connection()
            self.db.bulk_upsert_properties(items)
            logger.info("✅ Successfully processed and saved items")
        except Exception as e:
            logger.error(f"❌ Error processing items: {e}")
            raise

    def process_single_item(self, item: Property):
        """Processes and stores a single scraped property."""
        logger.info(f"Processing single item from {item.source_name}")
        try:
            self._ensure_connection()
            self.db.upsert_property(item)
            logger.info("✅ Successfully processed and saved item")
        except Exception as e:
            logger.error(f"❌ Error processing single item: {e}")
            raise

    def close(self):
        """Closes the DB connection manually."""
        if self.db:
            self.db.close()
            logger.info("ℹ️ Database connection closed successfully")
