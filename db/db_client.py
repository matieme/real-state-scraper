import psycopg2
from psycopg2.extras import execute_values
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DBClient:
    def __init__(self, host, database, user, password, port=5432):
        """Inicializa la conexión a la base de datos."""
        try:
            self.conn = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                port=port
            )
            self.cur = self.conn.cursor()
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def upsert_property(self, prop):
        """
        Inserta o actualiza una propiedad, y guarda historial de precio.
        Args:
            prop: Objeto Property con los datos del inmueble
        Returns:
            property_id: ID de la propiedad en la base de datos
        """
        try:
            # 1. Verificar si ya existe la propiedad
            self.cur.execute("""
                SELECT id FROM properties 
                WHERE source_name = %s AND source_identifier = %s
            """, (prop.source_name, prop.source_identifier))
            result = self.cur.fetchone()

            if result:
                property_id = result[0]
                # Actualizar datos de la propiedad
                self.cur.execute("""
                    UPDATE properties SET
                        location = %s,
                        exact_direction = %s,
                        total_surface = %s,
                        covered_surface = %s,
                        rooms = %s,
                        bedrooms = %s,
                        bathrooms = %s,
                        garages = %s,
                        age = %s,
                        layout = %s,
                        orientation = %s,
                        latitude = %s,
                        longitude = %s,
                        url = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    prop.location,
                    prop.exact_direction,
                    prop.total_surface,
                    prop.covered_surface,
                    prop.rooms,
                    prop.bedrooms,
                    prop.bathrooms,
                    prop.garages,
                    prop.age,
                    prop.layout,
                    prop.orientation,
                    prop.latitude,
                    prop.longitude,
                    prop.url,
                    property_id
                ))
            else:
                # Insertar nueva propiedad
                self.cur.execute("""
                    INSERT INTO properties (
                        source_name,
                        source_identifier,
                        location,
                        exact_direction,
                        total_surface,
                        covered_surface,
                        rooms,
                        bedrooms,
                        bathrooms,
                        garages,
                        age,
                        layout,
                        orientation,
                        latitude,
                        longitude,
                        url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    prop.source_name,
                    prop.source_identifier,
                    prop.location,
                    prop.exact_direction,
                    prop.total_surface,
                    prop.covered_surface,
                    prop.rooms,
                    prop.bedrooms,
                    prop.bathrooms,
                    prop.garages,
                    prop.age,
                    prop.layout,
                    prop.orientation,
                    prop.latitude,
                    prop.longitude,
                    prop.url
                ))
                property_id = self.cur.fetchone()[0]

            # 2. Verificar si el precio cambió
            self.cur.execute("""
                SELECT listing_price_amount 
                FROM price_history 
                WHERE source_identifier = %s AND source_name = %s
                ORDER BY scrape_date DESC LIMIT 1
            """, (prop.source_identifier, prop.source_name))
            last_price = self.cur.fetchone()

            if not last_price or last_price[0] != prop.price:
                self.insert_price_history(prop.source_identifier, prop.source_name, prop)

            self.conn.commit()
            return property_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error upserting property: {e}")
            raise

    def insert_price_history(self, source_identifier, source_name, prop):
        """
        Inserta un nuevo historial de precio.
        Args:
            source_identifier: Identificador único de la propiedad en la fuente original
            source_name: Nombre de la fuente de datos
            prop: Objeto Property con los datos del inmueble
        """
        try:
            self.cur.execute("""
                INSERT INTO price_history (
                    source_identifier,
                    source_name,
                    listing_price_amount,
                    listing_price_currency,
                    expenses,
                    expenses_currency,
                    sqr_price,
                    scrape_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                source_identifier,
                source_name,
                prop.price,
                prop.price_currency,
                prop.expenses,
                prop.expenses_currency,
                prop.sqr_price,
                datetime.fromisoformat(prop.scrape_date.replace('Z', '+00:00'))
            ))
        except Exception as e:
            logger.error(f"Error inserting price history: {e}")
            raise

    def bulk_upsert_properties(self, properties):
        """
        Inserta o actualiza múltiples propiedades en batch.
        Args:
            properties: Lista de objetos Property
        """
        try:
            for prop in properties:
                self.upsert_property(prop)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error in bulk upsert: {e}")
            raise

    def close(self):
        """Cierra la conexión a la base de datos."""
        try:
            self.cur.close()
            self.conn.close()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
            raise
