class Constants:
    ID = "Id"
    REFERENCE = "Reference"
    PRICE_CURRENCY = "Price Currency"
    PRICE = "Price"
    EXPENSES_CURRENCY = "Expenses Currency"
    EXPENSES = "Expenses"
    SQR_PRICE = "Square Meter Price"
    LOCATION = "Location"
    EXACT_LOCATION = "Exact Direction"
    TOTAL_SURFACE = "Total Surface"
    COVERED_SURFACE = "Covered Surface"
    ROOMS = "Rooms"
    BEDROOMS = "Bedrooms"
    BATHROOMS = "Bathrooms"
    GARAGES = "Garages"
    AGE = "Antiguedad"
    LAYOUT = "Disposicion"
    ORIENTATION = "Orientacion"

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
