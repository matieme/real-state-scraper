from utils.constants import Constants


class Property:
    def __init__(self, url="", price=None, expenses=None, location=None, exact_direction=None, total_surface=None,
                 covered_surface=None, rooms=None, bedrooms=None, bathrooms=None, garages=None, age=None, layout=None,
                 orientation=None):
        self.reference = url
        self.price = price
        self.expenses = expenses
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
            Constants.ID: self.reference,
            Constants.PRICE: self.price,
            Constants.EXPENSES: self.expenses,
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
