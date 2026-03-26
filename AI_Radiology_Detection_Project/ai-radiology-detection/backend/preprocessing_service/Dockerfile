FROM python:3.11-slim

RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-preprocess.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ config/
COPY database/ database/
COPY utils/ utils/
COPY preprocessing_service/ preprocessing_service/

RUN mkdir -p /app/uploads /app/processed
EXPOSE 5003
CMD ["python", "preprocessing_service/app.py"]
