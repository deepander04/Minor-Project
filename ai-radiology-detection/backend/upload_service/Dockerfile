FROM python:3.11-slim

WORKDIR /app
COPY requirements-upload.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ config/
COPY database/ database/
COPY utils/ utils/
COPY upload_service/ upload_service/

RUN mkdir -p /app/uploads
EXPOSE 5002
CMD ["python", "upload_service/app.py"]
