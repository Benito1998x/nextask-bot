# Usar Python 3.12 (slim es más ligero)
FROM python:3.12-slim

# Instalar dependencias del sistema operativo (opcional pero recomendado)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configurar el directorio de trabajo dentro del contenedor
WORKDIR /app

# Primero copiar solo requirements para cachear las capas de dependencias de Docker
# (Esto hace que si cambias el código, Docker no reinstale TODO).
COPY requirements.txt .

# Instalar las librerías
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . .

# Cloud Run y Render usan la variable de entorno PORT por defecto
# Exponemos el 8080 porque es el estándar de Google Cloud Run
ENV PORT=8080

# El comando de arranque usando Uvicorn (adaptado para contenedores)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
