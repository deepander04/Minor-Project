"""SQLAlchemy ORM models for the AI Radiology Detection system."""

import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Boolean, DateTime, Integer,
    BigInteger, Text, Numeric, ForeignKey, Enum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum('ADMIN', 'RADIOLOGIST', 'PHYSICIAN', 'LAB_TECH', name='user_role'), nullable=False, default='LAB_TECH')
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scans = relationship('Scan', back_populates='uploader')
    reports = relationship('Report', back_populates='reviewer')

    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'department': self.department,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Patient(Base):
    __tablename__ = 'patients'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(10))
    contact_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship('Scan', back_populates='patient')

    def to_dict(self):
        return {
            'id': str(self.id),
            'patient_id': self.patient_id,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'contact_number': self.contact_number
        }


class Scan(Base):
    __tablename__ = 'scans'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    modality = Column(Enum('XRAY', 'CT', 'MRI', 'ULTRASOUND', name='scan_modality'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    processed_path = Column(String(500))
    file_size_bytes = Column(BigInteger)
    file_format = Column(String(20), nullable=False)
    status = Column(Enum('UPLOADED', 'PREPROCESSING', 'ANALYZING', 'COMPLETED', 'FAILED', name='scan_status'), default='UPLOADED')
    notes = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    patient = relationship('Patient', back_populates='scans')
    uploader = relationship('User', back_populates='scans')
    ai_results = relationship('AIResult', back_populates='scan')
    reports = relationship('Report', back_populates='scan')

    def to_dict(self):
        return {
            'id': str(self.id),
            'patient_id': str(self.patient_id) if self.patient_id else None,
            'uploaded_by': str(self.uploaded_by) if self.uploaded_by else None,
            'modality': self.modality,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'processed_path': self.processed_path,
            'file_size_bytes': self.file_size_bytes,
            'file_format': self.file_format,
            'status': self.status,
            'notes': self.notes,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }


class AIModel(Base):
    __tablename__ = 'ai_models'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)
    modality = Column(Enum('XRAY', 'CT', 'MRI', 'ULTRASOUND', name='scan_modality'), nullable=False)
    version = Column(String(20), nullable=False)
    accuracy = Column(Numeric(5, 2))
    model_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    trained_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    results = relationship('AIResult', back_populates='model')

    def to_dict(self):
        return {
            'id': str(self.id),
            'model_name': self.model_name,
            'model_type': self.model_type,
            'modality': self.modality,
            'version': self.version,
            'accuracy': float(self.accuracy) if self.accuracy else None,
            'is_active': self.is_active
        }


class AIResult(Base):
    __tablename__ = 'ai_results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey('scans.id'))
    model_id = Column(UUID(as_uuid=True), ForeignKey('ai_models.id'))
    predicted_condition = Column(String(255), nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    heatmap_path = Column(String(500))
    inference_time_ms = Column(Integer)
    additional_findings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship('Scan', back_populates='ai_results')
    model = relationship('AIModel', back_populates='results')

    def to_dict(self):
        return {
            'id': str(self.id),
            'scan_id': str(self.scan_id),
            'model_id': str(self.model_id) if self.model_id else None,
            'predicted_condition': self.predicted_condition,
            'confidence_score': float(self.confidence_score),
            'heatmap_path': self.heatmap_path,
            'inference_time_ms': self.inference_time_ms,
            'additional_findings': self.additional_findings,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Report(Base):
    __tablename__ = 'reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey('scans.id'))
    ai_result_id = Column(UUID(as_uuid=True), ForeignKey('ai_results.id'))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    ai_prediction = Column(String(255))
    final_diagnosis = Column(String(255))
    radiologist_notes = Column(Text)
    status = Column(Enum('PENDING', 'APPROVED', 'OVERRIDDEN', name='report_status'), default='PENDING')
    report_pdf_path = Column(String(500))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship('Scan', back_populates='reports')
    reviewer = relationship('User', back_populates='reports')

    def to_dict(self):
        return {
            'id': str(self.id),
            'scan_id': str(self.scan_id),
            'ai_result_id': str(self.ai_result_id) if self.ai_result_id else None,
            'reviewed_by': str(self.reviewed_by) if self.reviewed_by else None,
            'ai_prediction': self.ai_prediction,
            'final_diagnosis': self.final_diagnosis,
            'radiologist_notes': self.radiologist_notes,
            'status': self.status,
            'report_pdf_path': self.report_pdf_path,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditLog(Base):
    __tablename__ = 'audit_log'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine(database_url):
    return create_engine(database_url)


def get_session(database_url):
    engine = get_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()
