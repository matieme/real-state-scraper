from utils.constants import Constants


class Property:
    def __init__(self, url="", reference=None, price_currency=None, price=None, expenses_currency=None, expenses=None, sqr_price=None, location=None, exact_direction=None, total_surface=None,
                 covered_surface=None, rooms=None, bedrooms=None, bathrooms=None, garages=None, age=None, layout=None,
                 orientation=None):
        self.id = url
        self.reference = reference
        self.price_currency = price_currency
        self.price = price
        self.expenses_currency = expenses_currency
        self.expenses = expenses
        self.sqr_price = sqr_price
        self.location = location
        self.exact_direction = exact_direction
        self.total_surface = total_surface
        self.covered_surface = covered_surface
        self.rooms = rooms
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.garages = garages
        self.age = age
        self.layout = layout
        self.orientation = orientation

    def to_dict(self):
        return {
            Constants.ID: self.id,
            Constants.REFERENCE: self.reference,
            Constants.PRICE_CURRENCY: self.price_currency,
            Constants.PRICE: self.price,
            Constants.EXPENSES_CURRENCY: self.expenses_currency,
            Constants.EXPENSES: self.expenses,
            Constants.SQR_PRICE: self.sqr_price,
            Constants.LOCATION: self.location,
            Constants.EXACT_LOCATION: self.exact_direction,
            Constants.TOTAL_SURFACE: self.total_surface,
            Constants.COVERED_SURFACE: self.covered_surface,
            Constants.ROOMS: self.rooms,
            Constants.BEDROOMS: self.bedrooms,
            Constants.BATHROOMS: self.bathrooms,
            Constants.GARAGES: self.garages,
            Constants.AGE: self.age,
            Constants.LAYOUT: self.layout,
            Constants.ORIENTATION: self.orientation,
        }
