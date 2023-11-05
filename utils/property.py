class Property:
    def __init__(self, url="", price=None, expenses=None, location=None, exact_direction=None, total_surface=None, covered_surface=None, rooms=None, bedrooms=None, bathrooms=None, garages=None, age=None, layout=None, orientation=None):
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
            "Referencia": self.reference,
            "Price": self.price,
            "Expenses": self.expenses,
            "Location": self.location,
            "Exact Direction": self.exact_direction,
            "Total Surface": self.total_surface,
            "Covered Surface": self.covered_surface,
            "Rooms": self.rooms,
            "Bedrooms": self.bedrooms,
            "Bathrooms": self.bathrooms,
            "Garages": self.garages,
            "Antiguedad": self.age,
            "Disposicion": self.layout,
            "Orientacion": self.orientation,
        }
