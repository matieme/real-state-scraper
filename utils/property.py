from utils.constants import Constants
from datetime import datetime, timezone

class Property:
    def __init__(self, url="", source_name=None, price_currency=None, price=None, expenses_currency=None, expenses=None,
                 sqr_price=None, location=None, exact_direction=None, total_surface=None,
                 covered_surface=None, rooms=None, bedrooms=None, bathrooms=None, garages=None, age=None, layout=None,
                 orientation=None, latitude=None, longitude=None, source_identifier=None, scrape_date=None):
        """
        Identification of the property
        """
        self.id = url
        self.source_name = source_name
        self.source_identifier = source_identifier
        self.scrape_date = scrape_date or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        """
        Offer of the property
        """
        self.price_currency = price_currency
        self.price = price
        self.expenses_currency = expenses_currency
        self.expenses = expenses
        self.sqr_price = sqr_price
        """
        Characteristics of the property
        """
        self.total_surface = total_surface
        self.covered_surface = covered_surface
        self.rooms = rooms
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.garages = garages
        self.layout = layout
        self.orientation = orientation
        self.age = age
        """
        Location of the property
        """
        self.location = location
        self.exact_direction = exact_direction
        self.latitude = latitude
        self.longitude = longitude

    def to_dict(self):
        """
        Convert Property object to dictionary with organized fields
        """
        return {
            # Identification of the property
            Constants.ID: self.id,
            Constants.SOURCE_NAME: self.source_name,
            Constants.SOURCE_IDENTIFIER: self.source_identifier,
            Constants.SCRAPE_DATE: self.scrape_date,

            # Offer of the property
            Constants.PRICE_CURRENCY: self.price_currency,
            Constants.PRICE: self.price,
            Constants.EXPENSES_CURRENCY: self.expenses_currency,
            Constants.EXPENSES: self.expenses,
            Constants.SQR_PRICE: self.sqr_price,

            # Characteristics of the property
            Constants.TOTAL_SURFACE: self.total_surface,
            Constants.COVERED_SURFACE: self.covered_surface,
            Constants.ROOMS: self.rooms,
            Constants.BEDROOMS: self.bedrooms,
            Constants.BATHROOMS: self.bathrooms,
            Constants.GARAGES: self.garages,
            Constants.LAYOUT: self.layout,
            Constants.ORIENTATION: self.orientation,
            Constants.AGE: self.age,

            # Location of the property
            Constants.LOCATION: self.location,
            Constants.EXACT_LOCATION: self.exact_direction,
            Constants.LATITUDE: self.latitude,
            Constants.LONGITUDE: self.longitude,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Property instance from a dictionary with Constants keys
        """
        FIELD_MAPPING = {
            Constants.ID: 'url',
            Constants.SOURCE_NAME: 'source_name',
            Constants.SOURCE_IDENTIFIER: 'source_identifier',
            Constants.SCRAPE_DATE: 'scrape_date',
            Constants.PRICE_CURRENCY: 'price_currency',
            Constants.PRICE: 'price',
            Constants.EXPENSES_CURRENCY: 'expenses_currency',
            Constants.EXPENSES: 'expenses',
            Constants.SQR_PRICE: 'sqr_price',
            Constants.TOTAL_SURFACE: 'total_surface',
            Constants.COVERED_SURFACE: 'covered_surface',
            Constants.ROOMS: 'rooms',
            Constants.BEDROOMS: 'bedrooms',
            Constants.BATHROOMS: 'bathrooms',
            Constants.GARAGES: 'garages',
            Constants.LAYOUT: 'layout',
            Constants.ORIENTATION: 'orientation',
            Constants.AGE: 'age',
            Constants.LOCATION: 'location',
            Constants.EXACT_LOCATION: 'exact_direction',
            Constants.LATITUDE: 'latitude',
            Constants.LONGITUDE: 'longitude',
        }
        init_kwargs = {FIELD_MAPPING[k]: v for k, v in data.items() if k in FIELD_MAPPING}
        return cls(**init_kwargs)
