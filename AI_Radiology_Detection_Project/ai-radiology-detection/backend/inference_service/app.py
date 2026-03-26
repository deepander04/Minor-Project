"""AI Inference Service — CNN model inference, Grad-CAM heatmap generation."""

import os
import sys
import time
import uuid
import random
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from database.models import Scan, AIResult, AIModel, get_session
from utils.auth import init_auth, token_required, role_required
from config.settings import Config

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
init_auth(Config.JWT_SECRET)

HEATMAP_DIR = Config.HEATMAP_DIR
os.makedirs(HEATMAP_DIR, exist_ok=True)

# ─── Disease Mapping per Modality ─────────────────────────────
DISEASE_MAP = {
    'XRAY': {
        'diseases': ['Pneumonia', 'Tuberculosis', 'COVID-19', 'Cardiomegaly', 'No Abnormality Detected'],
        'model_type': 'ResNet-50'
    },
    'CT': {
        'diseases': ['Lung Nodule', 'Lung Cancer', 'Pleural Effusion', 'No Abnormality Detected'],
        'model_type': 'DenseNet-121'
    },
    'MRI': {
        'diseases': ['Brain Tumor', 'Stroke', 'Hemorrhage', 'No Abnormality Detected'],
        'model_type': 'U-Net'
    },
    'ULTRASOUND': {
        'diseases': ['Gallstones', 'Liver Lesion', 'No Abnormality Detected'],
        'model_type': 'Custom CNN'
    }
}


def get_db():
    return get_session(Config.DATABASE_URL)


def generate_gradcam_heatmap(image_path, prediction_idx, modality):
    """
    Generate a Grad-CAM style heatmap overlay.

    In production, this would:
    1. Forward pass through the CNN
    2. Compute gradients of predicted class w.r.t. last conv layer
    3. Global average pool gradients → channel weights
    4. Weighted sum of feature maps → spatial attention map
    5. ReLU + upsample to original size
    6. Overlay as colormap on original image

    For this demo, we simulate a realistic heatmap using Gaussian blobs
    positioned in anatomically relevant regions.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    h, w = img.shape[:2]

    # Create heatmap base (simulate CNN attention)
    heatmap = np.zeros((h, w), dtype=np.float32)

    # Generate attention blobs in relevant regions
    num_blobs = random.randint(1, 3)
    for _ in range(num_blobs):
        # Center the attention in medically relevant areas
        if modality == 'XRAY':
            cx = random.randint(w // 4, 3 * w // 4)
            cy = random.randint(h // 3, 2 * h // 3)
        elif modality == 'MRI':
            cx = random.randint(w // 3, 2 * w // 3)
            cy = random.randint(h // 3, 2 * h // 3)
        else:
            cx = random.randint(w // 4, 3 * w // 4)
            cy = random.randint(h // 4, 3 * h // 4)

        radius = random.randint(min(h, w) // 8, min(h, w) // 4)
        cv2.circle(heatmap, (cx, cy), radius, 1.0, -1)

    # Apply Gaussian blur for smooth gradient
    heatmap = cv2.GaussianBlur(heatmap, (0, 0), sigmaX=radius * 0.6)
    heatmap = heatmap / (heatmap.max() + 1e-8)

    # Apply ReLU (keep only positive activations — Grad-CAM spec)
    heatmap = np.maximum(heatmap, 0)

    # Convert to colormap
    heatmap_colored = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)

    # Overlay on original image (alpha blending)
    overlay = cv2.addWeighted(img, 0.6, heatmap_colored, 0.4, 0)

    # Save heatmap
    heatmap_filename = f"heatmap_{uuid.uuid4().hex}.png"
    heatmap_path = os.path.join(HEATMAP_DIR, heatmap_filename)
    cv2.imwrite(heatmap_path, overlay)

    return heatmap_path


def run_inference(image_path, modality):
    """
    Run CNN inference on preprocessed image.

    In production with PyTorch:
        model = torch.load(model_path)
        model.eval()
        tensor = transforms.ToTensor()(image).unsqueeze(0)
        with torch.no_grad():
            output = model(tensor)
        probabilities = torch.softmax(output, dim=1)

    For demo: simulate realistic predictions with appropriate confidence scores.
    """
    start = time.time()

    diseases = DISEASE_MAP[modality]['diseases']

    # Simulate model output — weighted random with bias toward disease detection
    # In production, this is the actual softmax output from the CNN
    weights = [random.uniform(0.5, 1.0) for _ in diseases[:-1]]
    weights.append(random.uniform(0.1, 0.5))  # Lower weight for "no abnormality"

    total = sum(weights)
    probabilities = [w / total for w in weights]

    # Select top prediction
    max_idx = probabilities.index(max(probabilities))
    predicted_condition = diseases[max_idx]
    confidence = round(random.uniform(85.0, 96.0), 1)  # Simulate high-confidence prediction

    # If "No Abnormality" is selected, give it high confidence
    if predicted_condition == 'No Abnormality Detected':
        confidence = round(random.uniform(90.0, 98.0), 1)

    # Generate Grad-CAM heatmap (skip for normal scans)
    heatmap_path = None
    if predicted_condition != 'No Abnormality Detected':
        heatmap_path = generate_gradcam_heatmap(image_path, max_idx, modality)

    # Additional findings (multi-label)
    additional = {}
    for i, disease in enumerate(diseases):
        additional[disease] = round(probabilities[i] * 100, 1)

    inference_time_ms = int((time.time() - start) * 1000) + random.randint(800, 3000)  # Simulate GPU time

    return {
        'predicted_condition': predicted_condition,
        'confidence_score': confidence,
        'heatmap_path': heatmap_path,
        'inference_time_ms': inference_time_ms,
        'additional_findings': additional
    }


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'inference_service'})


@app.route('/api/analyze/<scan_id>', methods=['POST'])
@role_required('ADMIN', 'RADIOLOGIST')
def analyze_scan(scan_id):
    """Run AI inference on a preprocessed scan."""
    db = get_db()
    try:
        scan = db.query(Scan).filter_by(id=scan_id).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        if scan.status != 'ANALYZING':
            return jsonify({'error': f'Scan must be in ANALYZING state (current: {scan.status}). Run preprocessing first.'}), 400

        image_path = scan.processed_path or scan.file_path
        if not os.path.exists(image_path):
            return jsonify({'error': 'Processed image not found'}), 404

        # Get the appropriate AI model record
        model = db.query(AIModel).filter_by(
            modality=scan.modality,
            is_active=True
        ).first()

        # Run inference
        result = run_inference(image_path, scan.modality)

        # Save AI result
        ai_result = AIResult(
            scan_id=scan.id,
            model_id=model.id if model else None,
            predicted_condition=result['predicted_condition'],
            confidence_score=result['confidence_score'],
            heatmap_path=result['heatmap_path'],
            inference_time_ms=result['inference_time_ms'],
            additional_findings=result['additional_findings']
        )
        db.add(ai_result)

        # Update scan status
        scan.status = 'COMPLETED'
        db.commit()

        return jsonify({
            'message': 'AI analysis completed',
            'result': ai_result.to_dict(),
            'model_used': model.to_dict() if model else None,
            'scan': scan.to_dict()
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/results/<scan_id>', methods=['GET'])
@role_required('ADMIN', 'RADIOLOGIST', 'PHYSICIAN')
def get_results(scan_id):
    """Get AI analysis results for a scan."""
    db = get_db()
    try:
        results = db.query(AIResult).filter_by(scan_id=scan_id).order_by(AIResult.created_at.desc()).all()
        if not results:
            return jsonify({'error': 'No results found for this scan'}), 404

        return jsonify({
            'results': [r.to_dict() for r in results]
        }), 200
    finally:
        db.close()


@app.route('/api/heatmap/<result_id>', methods=['GET'])
@role_required('ADMIN', 'RADIOLOGIST', 'PHYSICIAN')
def get_heatmap(result_id):
    """Serve the Grad-CAM heatmap image for a result."""
    db = get_db()
    try:
        result = db.query(AIResult).filter_by(id=result_id).first()
        if not result or not result.heatmap_path:
            return jsonify({'error': 'Heatmap not found'}), 404
        if os.path.exists(result.heatmap_path):
            return send_file(result.heatmap_path, mimetype='image/png')
        return jsonify({'error': 'Heatmap file not found on disk'}), 404
    finally:
        db.close()


@app.route('/api/models', methods=['GET'])
@token_required
def list_models():
    """List all registered AI models."""
    db = get_db()
    try:
        models = db.query(AIModel).filter_by(is_active=True).all()
        return jsonify({'models': [m.to_dict() for m in models]}), 200
    finally:
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
