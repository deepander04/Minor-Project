FROM python:3.11-slim

WORKDIR /app
COPY requirements-auth.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ config/
COPY database/ database/
COPY utils/ utils/
COPY auth_service/ auth_service/

EXPOSE 5001
CMD ["python", "auth_service/app.py"]
