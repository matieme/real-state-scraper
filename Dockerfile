# Imagen base de Python 3.11 con sistema minimalista
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema para Playwright y Chromium
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxrandr2 \
    libxfixes3 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos del proyecto
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Instala solo playwright y chromium
RUN pip install --no-cache-dir playwright && playwright install chromium --with-deps

COPY . .

# Crear carpeta de resultados si aún se usa
RUN mkdir -p results

# Variables de entorno de ejecución
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Comando de entrada
CMD ["python", "main.py"]
