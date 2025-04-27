-- Tabla principal de propiedades
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    source_identifier VARCHAR(100),
    location TEXT,
    exact_direction TEXT,
    total_surface NUMERIC,
    covered_surface NUMERIC,
    rooms INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    garages INTEGER,
    age TEXT,
    layout TEXT,
    orientation TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(id, source_name)
);

-- Tabla de historial de precios
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id),
    listing_price_amount NUMERIC NOT NULL,
    listing_price_currency VARCHAR(3) NOT NULL,
    expenses NUMERIC,
    expenses_currency VARCHAR(3),
    sqr_price NUMERIC,
    scrape_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar performance
CREATE INDEX idx_properties_source ON properties(source_name, source_identifier);
CREATE INDEX idx_price_history_property ON price_history(property_id);
CREATE INDEX idx_price_history_date ON price_history(scrape_date); 