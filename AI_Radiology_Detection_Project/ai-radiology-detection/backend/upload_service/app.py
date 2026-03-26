"""Upload Service — Medical image upload with format/size validation."""

import os
import sys
import uuid
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from database.models import Scan, Patient, get_session
from utils.auth import init_auth, token_required, role_required
from config.settings import Config

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
init_auth(Config.JWT_SECRET)

UPLOAD_DIR = Config.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    return get_session(Config.DATABASE_URL)


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in Config.ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'upload_service'})


@app.route('/api/upload', methods=['POST'])
@role_required('ADMIN', 'RADIOLOGIST', 'LAB_TECH')
def upload_image():
    """Upload a medical image for AI analysis."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Invalid file format. Please upload JPEG, PNG, or DICOM.'
        }), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > Config.MAX_FILE_SIZE:
        return jsonify({
            'error': f'File exceeds maximum allowed size of {Config.MAX_FILE_SIZE // (1024*1024)}MB.'
        }), 400

    # Validate required fields
    patient_id = request.form.get('patient_id')
    modality = request.form.get('modality')
    if not patient_id or not modality:
        return jsonify({'error': 'patient_id and modality are required'}), 400

    if modality not in ('XRAY', 'CT', 'MRI', 'ULTRASOUND'):
        return jsonify({'error': 'Please select a scan type to proceed.'}), 400

    db = get_db()
    try:
        # Verify patient exists
        patient = db.query(Patient).filter_by(patient_id=patient_id).first()
        if not patient:
            return jsonify({'error': f'Patient {patient_id} not found'}), 404

        # Save file
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        file.save(file_path)

        # Create scan record
        scan = Scan(
            patient_id=patient.id,
            uploaded_by=request.user['user_id'],
            modality=modality,
            original_filename=secure_filename(file.filename),
            file_path=file_path,
            file_size_bytes=file_size,
            file_format=ext.upper(),
            status='UPLOADED',
            notes=request.form.get('notes', '')
        )
        db.add(scan)
        db.commit()

        return jsonify({
            'message': 'Image uploaded successfully',
            'scan': scan.to_dict(),
            'patient': patient.to_dict()
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/scans', methods=['GET'])
@token_required
def list_scans():
    """List scans based on user role and optional filters."""
    db = get_db()
    try:
        query = db.query(Scan)

        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(Scan.status == status)

        # Filter by modality
        modality = request.args.get('modality')
        if modality:
            query = query.filter(Scan.modality == modality)

        scans = query.order_by(Scan.uploaded_at.desc()).limit(50).all()
        return jsonify({'scans': [s.to_dict() for s in scans]}), 200
    finally:
        db.close()


@app.route('/api/scans/<scan_id>', methods=['GET'])
@token_required
def get_scan(scan_id):
    """Get a specific scan by ID."""
    db = get_db()
    try:
        scan = db.query(Scan).filter_by(id=scan_id).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        return jsonify({'scan': scan.to_dict()}), 200
    finally:
        db.close()


@app.route('/api/scans/<scan_id>/image', methods=['GET'])
@token_required
def get_scan_image(scan_id):
    """Serve the original uploaded scan image."""
    db = get_db()
    try:
        scan = db.query(Scan).filter_by(id=scan_id).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        if os.path.exists(scan.file_path):
            return send_file(scan.file_path)
        return jsonify({'error': 'Image file not found'}), 404
    finally:
        db.close()


@app.route('/api/patients', methods=['GET'])
@token_required
def list_patients():
    """List all patients."""
    db = get_db()
    try:
        patients = db.query(Patient).order_by(Patient.created_at.desc()).all()
        return jsonify({'patients': [p.to_dict() for p in patients]}), 200
    finally:
        db.close()


@app.route('/api/patients', methods=['POST'])
@role_required('ADMIN', 'RADIOLOGIST', 'LAB_TECH')
def create_patient():
    """Create a new patient record."""
    data = request.get_json()
    required = ['patient_id', 'full_name']
    if not all(k in data for k in required):
        return jsonify({'error': 'patient_id and full_name are required'}), 400

    db = get_db()
    try:
        existing = db.query(Patient).filter_by(patient_id=data['patient_id']).first()
        if existing:
            return jsonify({'error': 'Patient ID already exists'}), 409

        patient = Patient(
            patient_id=data['patient_id'],
            full_name=data['full_name'],
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            contact_number=data.get('contact_number')
        )
        db.add(patient)
        db.commit()
        return jsonify({'message': 'Patient created', 'patient': patient.to_dict()}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
