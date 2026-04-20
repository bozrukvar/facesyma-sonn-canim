FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    fastapi==0.115.0 uvicorn==0.30.6 \
    httpx==0.27.2 pymongo==4.7.2 \
    PyJWT==2.9.0 python-multipart==0.0.12
COPY main.py .
EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
