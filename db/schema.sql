-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tabla principal de propiedades
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    source_identifier VARCHAR(100) NOT NULL,
    url TEXT,
    scrape_date TIMESTAMP WITH TIME ZONE NOT NULL,
    listing_price_amount NUMERIC NOT NULL,
    listing_price_currency VARCHAR(3) NOT NULL,
    expenses NUMERIC,
    expenses_currency VARCHAR(3),
    sqr_price NUMERIC,
    total_surface NUMERIC,
    covered_surface NUMERIC,
    rooms INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    garages INTEGER,
    amenities TEXT[],
    layout TEXT,
    orientation TEXT,
    age INTEGER NULL,
    country TEXT DEFAULT 'Argentina',
    state TEXT DEFAULT 'Buenos Aires',
    city TEXT DEFAULT 'Capital Federal',
    zone TEXT,
    address TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    location GEOGRAPHY(POINT, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name, source_identifier)
);

-- Tabla de historial de precios (guarda sólo cuando el precio cambia)
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    source_identifier VARCHAR(100) NOT NULL,
    listing_price_amount NUMERIC NOT NULL,
    listing_price_currency VARCHAR(3) NOT NULL,
    expenses NUMERIC,
    expenses_currency VARCHAR(3),
    sqr_price NUMERIC,
    scrape_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name, source_identifier, scrape_date)
);

-- Índices para mejorar performance
CREATE INDEX idx_properties_source ON properties(source_name, source_identifier);
CREATE INDEX idx_price_history_source ON price_history(source_name, source_identifier);
CREATE INDEX idx_price_history_date ON price_history(scrape_date);