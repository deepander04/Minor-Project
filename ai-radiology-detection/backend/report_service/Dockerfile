FROM python:3.11-slim

WORKDIR /app
COPY requirements-report.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ config/
COPY database/ database/
COPY utils/ utils/
COPY report_service/ report_service/

RUN mkdir -p /app/reports /app/heatmaps
EXPOSE 5005
CMD ["python", "report_service/app.py"]
