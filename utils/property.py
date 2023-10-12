class Property:
    def __init__(self, href, price, location, total_surface, covered_surface, rooms, bedrooms, bathrooms, garages,
                 features=None):
        self.href = href
        self.price = price
        self.location = location
        self.total_surface = total_surface
        self.covered_surface = covered_surface
        self.rooms = rooms
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.garages = garages
        self.features = features or []

    def __str__(self):
        return f"Property(href={self.href}, price={self.price}, location={self.location}, total_surface={self.total_surface}, covered_surface={self.covered_surface},rooms={self.rooms},bedrooms={self.bedrooms},bathrooms={self.bathrooms},garages={self.garages},features={self.features})"
