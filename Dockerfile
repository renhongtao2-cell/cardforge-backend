FROM python:3.12-slim AS backend

WORKDIR /app

<<<<<<< HEAD
# Install system dependencies for Pillow (skip fonts to save memory)
RUN apt-get update && apt-get install -y --no-install-recommends \
=======
# Install system dependencies for Pillow
RUN apt-get update && apt-get install -y \
>>>>>>> 22652ddea2dcf88cc3a38bb9eaad33ff332f5d86
    gcc \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
<<<<<<< HEAD
=======
    ttf-mscorefonts-installer \
>>>>>>> 22652ddea2dcf88cc3a38bb9eaad33ff332f5d86
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY routes/ ./routes/
COPY services/ ./services/

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8000

<<<<<<< HEAD
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
=======
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
>>>>>>> 22652ddea2dcf88cc3a38bb9eaad33ff332f5d86
