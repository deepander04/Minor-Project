"""Preprocessing Service — Image normalization, resizing, noise reduction pipeline."""

import os
import sys
import time
import uuid
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cv2
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from database.models import Scan, get_session
from utils.auth import init_auth, token_required, role_required
from config.settings import Config

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
init_auth(Config.JWT_SECRET)

PROCESSED_DIR = Config.PROCESSED_DIR
os.makedirs(PROCESSED_DIR, exist_ok=True)


def get_db():
    return get_session(Config.DATABASE_URL)


def preprocess_image(file_path, modality):
    """
    Full preprocessing pipeline:
    1. Read image (grayscale for X-ray, color for others)
    2. CLAHE contrast enhancement
    3. Gaussian noise reduction
    4. Resize to model input dimensions
    5. Normalize pixel values to [0, 1]
    """
    start = time.time()

    # Read image
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE if modality in ('XRAY',) else cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {file_path}")

    # CLAHE contrast enhancement (especially useful for X-rays)
    if len(img.shape) == 2:  # Grayscale
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
    else:  # Color
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img = cv2.merge([l, a, b])
        img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)

    # Gaussian blur for noise reduction
    img = cv2.GaussianBlur(img, (3, 3), 0)

    # Resize based on modality
    target_size = Config.UNET_DIMENSION if modality == 'MRI' else Config.MAX_IMAGE_DIMENSION
    img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)

    # Normalize to [0, 1] range
    img_normalized = img.astype(np.float32) / 255.0

    # Save processed image (as 8-bit for visualization)
    processed_filename = f"processed_{uuid.uuid4().hex}.png"
    processed_path = os.path.join(PROCESSED_DIR, processed_filename)
    cv2.imwrite(processed_path, (img_normalized * 255).astype(np.uint8))

    elapsed_ms = int((time.time() - start) * 1000)
    return processed_path, elapsed_ms, target_size


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'preprocessing_service'})


@app.route('/api/preprocess/<scan_id>', methods=['POST'])
@role_required('ADMIN', 'RADIOLOGIST', 'LAB_TECH')
def preprocess_scan(scan_id):
    """Preprocess a specific uploaded scan."""
    db = get_db()
    try:
        scan = db.query(Scan).filter_by(id=scan_id).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        if scan.status != 'UPLOADED':
            return jsonify({'error': f'Scan is already in {scan.status} state'}), 400

        if not os.path.exists(scan.file_path):
            return jsonify({'error': 'Original image file not found on disk'}), 404

        # Update status
        scan.status = 'PREPROCESSING'
        db.commit()

        # Run preprocessing
        processed_path, elapsed_ms, target_size = preprocess_image(scan.file_path, scan.modality)

        # Update scan record
        scan.processed_path = processed_path
        scan.status = 'ANALYZING'  # Ready for AI inference
        scan.processed_at = datetime.utcnow()
        db.commit()

        return jsonify({
            'message': 'Image preprocessed successfully',
            'scan_id': str(scan.id),
            'processed_path': processed_path,
            'processing_time_ms': elapsed_ms,
            'target_dimensions': f'{target_size}x{target_size}',
            'status': scan.status
        }), 200

    except ValueError as e:
        scan.status = 'FAILED'
        db.commit()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/preprocess/batch', methods=['POST'])
@role_required('ADMIN', 'RADIOLOGIST')
def preprocess_batch():
    """Preprocess all scans with UPLOADED status."""
    db = get_db()
    try:
        scans = db.query(Scan).filter_by(status='UPLOADED').all()
        results = []

        for scan in scans:
            try:
                scan.status = 'PREPROCESSING'
                db.commit()

                processed_path, elapsed_ms, target_size = preprocess_image(scan.file_path, scan.modality)
                scan.processed_path = processed_path
                scan.status = 'ANALYZING'
                scan.processed_at = datetime.utcnow()
                db.commit()

                results.append({
                    'scan_id': str(scan.id),
                    'status': 'success',
                    'processing_time_ms': elapsed_ms
                })
            except Exception as e:
                scan.status = 'FAILED'
                db.commit()
                results.append({
                    'scan_id': str(scan.id),
                    'status': 'failed',
                    'error': str(e)
                })

        return jsonify({
            'message': f'Processed {len(results)} scans',
            'results': results
        }), 200
    finally:
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
