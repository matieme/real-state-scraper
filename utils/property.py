from utils.constants import Constants
from datetime import datetime, timezone

class Property:
    def __init__(self, url="", source_name=None, price_currency=None, price=None, expenses_currency=None, expenses=None,
                 sqr_price=None, country=None, state=None, city=None, zone=None, address=None, total_surface=None,
                 covered_surface=None, rooms=None, bedrooms=None, bathrooms=None, garages=None, amenities=None, age=None, layout=None,
                 orientation=None, latitude=None, longitude=None, location=None, source_identifier=None, scrape_date=None):
        """
        Identification of the property
        """
        self.source_name = source_name
        self.source_identifier = source_identifier
        self.url = url
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
        self.amenities = amenities or []
        self.layout = layout
        self.orientation = orientation
        self.age = age
        """
        Location of the property
        """
        self.country = country
        self.state = state
        self.city = city
        self.zone = zone
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.location = location

    def to_dict(self):
        """
        Convert Property object to dictionary with organized fields
        """
        return {
            # Identification of the property
            Constants.URL: self.url,
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
            Constants.AMENITIES: self.amenities,
            Constants.LAYOUT: self.layout,
            Constants.ORIENTATION: self.orientation,
            Constants.AGE: self.age,

            # Location of the property
            Constants.COUNTRY: self.country,
            Constants.STATE: self.state,
            Constants.CITY: self.city,
            Constants.ZONE: self.zone,
            Constants.ADDRESS: self.address,
            Constants.LATITUDE: self.latitude,
            Constants.LONGITUDE: self.longitude,
            Constants.LOCATION: self.location,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Property instance from a dictionary with Constants keys
        """
        FIELD_MAPPING = {
            Constants.URL: 'url',
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
            Constants.AMENITIES: 'amenities',
            Constants.LAYOUT: 'layout',
            Constants.ORIENTATION: 'orientation',
            Constants.AGE: 'age',
            Constants.COUNTRY: 'country',
            Constants.STATE: 'state',
            Constants.CITY: 'city',
            Constants.ZONE: 'zone',
            Constants.ADDRESS: 'address',
            Constants.LATITUDE: 'latitude',
            Constants.LONGITUDE: 'longitude',
            Constants.LOCATION: 'location',
        }
        init_kwargs = {FIELD_MAPPING[k]: v for k, v in data.items() if k in FIELD_MAPPING}
        return cls(**init_kwargs)
