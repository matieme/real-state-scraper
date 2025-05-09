class Constants:
    ID = "Id"
    URL = "Url"
    SOURCE_NAME = "Source Name"
    SOURCE_IDENTIFIER = "SourceIdentifier"
    SCRAPE_DATE = "ScrapeDate"
    PRICE_CURRENCY = "PriceCurrency"
    PRICE = "Price"
    EXPENSES_CURRENCY = "ExpensesCurrency"
    EXPENSES = "Expenses"
    SQR_PRICE = "SquareMeterPrice"
    COUNTRY = "Country"
    STATE = "State"
    CITY = "City"
    ZONE = "Zone"
    ADDRESS = "Address"
    TOTAL_SURFACE = "TotalSurface"
    COVERED_SURFACE = "CoveredSurface"
    ROOMS = "Rooms"
    BEDROOMS = "Bedrooms"
    BATHROOMS = "Bathrooms"
    GARAGES = "Garages"
    AGE = "Age"
    LAYOUT = "Layout"
    ORIENTATION = "Orientation"
    LATITUDE = "Latitude"
    LONGITUDE = "Longitude"

    ARGENPROP_FEATURE_MAPPING = {
        "icono-superficie_total": TOTAL_SURFACE,
        "icono-superficie_cubierta": COVERED_SURFACE,
        "icono-cantidad_ambientes": ROOMS,
        "icono-cantidad_dormitorios": BEDROOMS,
        "icono-cantidad_banos": BATHROOMS,
        "icono-ambiente_cochera": GARAGES,
        "icono-antiguedad": AGE,
        "icono-disposicion": LAYOUT,
        "icono-orientacion": ORIENTATION,
    }

    ZONAPROP_FEATURE_MAPPING = {
        "icon-stotal": TOTAL_SURFACE,
        "icon-scubierta": COVERED_SURFACE,
        "icon-ambiente": ROOMS,
        "icon-dormitorio": BEDROOMS,
        "icon-bano": BATHROOMS,
        "icon-cochera": GARAGES,
        "icon-antiguedad": AGE,
        "icon-disposicion": LAYOUT,
        "icon-orientacion": ORIENTATION,
    }

    MERCADOLIBRE_FEATURE_MAPPING = {
        "MAINTENANCE_FEE": EXPENSES,
        "TOTAL_AREA": TOTAL_SURFACE,
        "COVERED_AREA": COVERED_SURFACE,
        "ROOMS": ROOMS,
        "BEDROOMS": BEDROOMS,
        "FULL_BATHROOMS": BATHROOMS,
        "PARKING_LOTS": GARAGES,
        "PROPERTY_AGE": AGE,
        "DISPOSITION": LAYOUT,
        "FACING": ORIENTATION
    }

    ORIENTATION_MAPPING = {
        # Norte
        "norte": "N",
        "n": "N",
        "north": "N",
        # Noreste
        "noreste": "NE",
        "ne": "NE",
        "northeast": "NE",
        # Este
        "este": "E",
        "e": "E",
        "east": "E",
        # Noroeste
        "noroeste": "NO",
        "no": "NO",
        "northwest": "NO",
        # Oeste
        "oeste": "O",
        "o": "O",
        "west": "O",
        # Sur
        "sur": "S",
        "s": "S",
        "south": "S",
        # Sureste
        "sureste": "SE",
        "se": "SE",
        "southeast": "SE",
        # Suroeste
        "suroeste": "SO",
        "so": "SO",
        "southwest": "SO"
    }

    LAYOUT_MAPPING = {
        # Frente
        "frente": "Frente",
        "f": "Frente",
        # Contrafrente
        "contra frente": "Contrafrente",
        "contrafrente": "Contrafrente",
        "contra-frente": "Contrafrente",
        "contra": "Contrafrente",
        "cf": "Contrafrente",
        # Lateral
        "lateral": "Lateral",
        "l": "Lateral"
    }
