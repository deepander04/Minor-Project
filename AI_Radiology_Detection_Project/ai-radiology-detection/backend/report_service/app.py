"""Report Service — PDF diagnostic report generation, radiologist review & override."""

import os
import sys
import uuid
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from database.models import Report, Scan, AIResult, Patient, User, get_session
from utils.auth import init_auth, token_required, role_required
from config.settings import Config

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
init_auth(Config.JWT_SECRET)

REPORT_DIR = Config.REPORT_DIR
os.makedirs(REPORT_DIR, exist_ok=True)


def get_db():
    return get_session(Config.DATABASE_URL)


def generate_pdf_report(report, scan, ai_result, patient, reviewer):
    """Generate a professional PDF diagnostic report."""
    pdf_filename = f"report_{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(REPORT_DIR, pdf_filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=18, spaceAfter=20,
                                  textColor=colors.HexColor('#1a365d'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                    fontSize=13, spaceAfter=10,
                                    textColor=colors.HexColor('#2d3748'))
    body_style = styles['Normal']

    elements = []

    # Header
    elements.append(Paragraph("AI-Powered Radiology Detection", title_style))
    elements.append(Paragraph("Diagnostic Report", heading_style))
    elements.append(Spacer(1, 12))

    # Report metadata
    meta_data = [
        ['Report ID:', str(report.id)[:8].upper()],
        ['Date:', report.created_at.strftime('%B %d, %Y %H:%M') if report.created_at else 'N/A'],
        ['Status:', report.status],
    ]
    meta_table = Table(meta_data, colWidths=[1.5*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 18))

    # Patient Information
    elements.append(Paragraph("Patient Information", heading_style))
    patient_data = [
        ['Patient ID:', patient.patient_id if patient else 'N/A'],
        ['Full Name:', patient.full_name if patient else 'N/A'],
        ['Gender:', patient.gender if patient else 'N/A'],
        ['Date of Birth:', patient.date_of_birth.strftime('%Y-%m-%d') if patient and patient.date_of_birth else 'N/A'],
    ]
    patient_table = Table(patient_data, colWidths=[1.5*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 18))

    # Scan Details
    elements.append(Paragraph("Scan Details", heading_style))
    scan_data = [
        ['Modality:', scan.modality if scan else 'N/A'],
        ['Original File:', scan.original_filename if scan else 'N/A'],
        ['Upload Date:', scan.uploaded_at.strftime('%Y-%m-%d %H:%M') if scan and scan.uploaded_at else 'N/A'],
    ]
    scan_table = Table(scan_data, colWidths=[1.5*inch, 4*inch])
    scan_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(scan_table)
    elements.append(Spacer(1, 18))

    # AI Analysis Results
    elements.append(Paragraph("AI Analysis Results", heading_style))
    ai_data = [
        ['AI Prediction:', report.ai_prediction or (ai_result.predicted_condition if ai_result else 'N/A')],
        ['Confidence Score:', f"{float(ai_result.confidence_score):.1f}%" if ai_result else 'N/A'],
        ['Inference Time:', f"{ai_result.inference_time_ms}ms" if ai_result else 'N/A'],
        ['Model Used:', ai_result.model_id if ai_result else 'N/A'],
    ]
    ai_table = Table(ai_data, colWidths=[1.5*inch, 4*inch])
    ai_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(ai_table)
    elements.append(Spacer(1, 18))

    # Heatmap image (if available)
    if ai_result and ai_result.heatmap_path and os.path.exists(ai_result.heatmap_path):
        elements.append(Paragraph("Grad-CAM Heatmap Visualization", heading_style))
        try:
            img = RLImage(ai_result.heatmap_path, width=4*inch, height=4*inch)
            elements.append(img)
            elements.append(Spacer(1, 12))
        except Exception:
            elements.append(Paragraph("(Heatmap image could not be embedded)", body_style))

    # Final Diagnosis (Radiologist)
    elements.append(Paragraph("Radiologist Final Diagnosis", heading_style))
    diag_data = [
        ['Final Diagnosis:', report.final_diagnosis or 'Pending'],
        ['Reviewed By:', reviewer.full_name if reviewer else 'Pending'],
        ['Clinical Notes:', report.radiologist_notes or 'None'],
        ['Review Date:', report.reviewed_at.strftime('%Y-%m-%d %H:%M') if report.reviewed_at else 'Pending'],
    ]
    diag_table = Table(diag_data, colWidths=[1.5*inch, 4*inch])
    diag_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(diag_table)
    elements.append(Spacer(1, 24))

    # Disclaimer
    disclaimer_style = ParagraphStyle('Disclaimer', parent=body_style,
                                       fontSize=8, textColor=colors.grey)
    elements.append(Paragraph(
        "DISCLAIMER: This report is generated by an AI-assisted decision-support system. "
        "The AI prediction is preliminary and must be validated by a licensed radiologist. "
        "Final clinical decisions are made by the reviewing physician. "
        "This system is not a replacement for professional medical judgment.",
        disclaimer_style
    ))

    doc.build(elements)
    return pdf_path


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'report_service'})


@app.route('/api/reports', methods=['POST'])
@role_required('ADMIN', 'RADIOLOGIST')
def create_report():
    """Create a new report (radiologist submits diagnosis)."""
    data = request.get_json()
    required = ['scan_id', 'final_diagnosis']
    if not all(k in data for k in required):
        return jsonify({'error': 'scan_id and final_diagnosis are required'}), 400

    db = get_db()
    try:
        scan = db.query(Scan).filter_by(id=data['scan_id']).first()
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        # Get latest AI result for this scan
        ai_result = db.query(AIResult).filter_by(scan_id=scan.id).order_by(AIResult.created_at.desc()).first()

        # Determine report status
        ai_prediction = ai_result.predicted_condition if ai_result else None
        status = 'APPROVED' if data['final_diagnosis'] == ai_prediction else 'OVERRIDDEN'

        # Get patient and reviewer info
        patient = db.query(Patient).filter_by(id=scan.patient_id).first()
        reviewer = db.query(User).filter_by(id=request.user['user_id']).first()

        report = Report(
            scan_id=scan.id,
            ai_result_id=ai_result.id if ai_result else None,
            reviewed_by=request.user['user_id'],
            ai_prediction=ai_prediction,
            final_diagnosis=data['final_diagnosis'],
            radiologist_notes=data.get('notes', ''),
            status=status,
            reviewed_at=datetime.utcnow()
        )
        db.add(report)
        db.commit()

        # Generate PDF
        pdf_path = generate_pdf_report(report, scan, ai_result, patient, reviewer)
        report.report_pdf_path = pdf_path
        db.commit()

        return jsonify({
            'message': 'Report created successfully',
            'report': report.to_dict(),
            'status': status
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/reports', methods=['GET'])
@role_required('ADMIN', 'RADIOLOGIST', 'PHYSICIAN')
def list_reports():
    """List reports. Physicians see only their patients' reports."""
    db = get_db()
    try:
        query = db.query(Report)

        # Filter by scan_id
        scan_id = request.args.get('scan_id')
        if scan_id:
            query = query.filter(Report.scan_id == scan_id)

        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(Report.status == status)

        reports = query.order_by(Report.created_at.desc()).limit(50).all()
        return jsonify({'reports': [r.to_dict() for r in reports]}), 200
    finally:
        db.close()


@app.route('/api/reports/<report_id>', methods=['GET'])
@role_required('ADMIN', 'RADIOLOGIST', 'PHYSICIAN')
def get_report(report_id):
    """Get a specific report."""
    db = get_db()
    try:
        report = db.query(Report).filter_by(id=report_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        return jsonify({'report': report.to_dict()}), 200
    finally:
        db.close()


@app.route('/api/reports/<report_id>/pdf', methods=['GET'])
@role_required('ADMIN', 'RADIOLOGIST', 'PHYSICIAN')
def download_report_pdf(report_id):
    """Download the PDF report."""
    db = get_db()
    try:
        report = db.query(Report).filter_by(id=report_id).first()
        if not report or not report.report_pdf_path:
            return jsonify({'error': 'Report PDF not found'}), 404
        if os.path.exists(report.report_pdf_path):
            return send_file(report.report_pdf_path, as_attachment=True,
                           download_name=f'diagnostic_report_{str(report.id)[:8]}.pdf')
        return jsonify({'error': 'PDF file not found on disk'}), 404
    finally:
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
