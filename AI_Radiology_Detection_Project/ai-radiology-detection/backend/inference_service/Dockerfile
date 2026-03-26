FROM python:3.11-slim

RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-inference.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ config/
COPY database/ database/
COPY utils/ utils/
COPY inference_service/ inference_service/

RUN mkdir -p /app/models /app/processed /app/heatmaps
EXPOSE 5004
CMD ["python", "inference_service/app.py"]
