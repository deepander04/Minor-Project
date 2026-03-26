import os

class Config:
    """Base configuration shared across all microservices."""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://radiology_user:radiology_pass_2026@localhost:5432/radiology_db')
    JWT_SECRET = os.getenv('JWT_SECRET', 'radiology-jwt-secret-key-2026')
    JWT_EXPIRY_HOURS = 24
    UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/app/uploads')
    PROCESSED_DIR = os.getenv('PROCESSED_DIR', '/app/processed')
    HEATMAP_DIR = os.getenv('HEATMAP_DIR', '/app/heatmaps')
    REPORT_DIR = os.getenv('REPORT_DIR', '/app/reports')
    MODEL_DIR = os.getenv('MODEL_DIR', '/app/models')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 52428800))  # 50MB
    ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png', 'dcm', 'dicom'}
    MAX_IMAGE_DIMENSION = 224  # ResNet/DenseNet input size
    UNET_DIMENSION = 256       # U-Net input size
