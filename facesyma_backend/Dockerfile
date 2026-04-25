FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libgomp1 libglib2.0-0 libsm6 libxext6 libxrender-dev wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Force cache invalidation - assessment views update
RUN echo "assessment views updated"

# Media klasörü
RUN mkdir -p media/tmp

EXPOSE 8000

CMD ["gunicorn", "facesyma_project.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120"]
