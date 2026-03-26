-- ============================================================
-- AI-Powered Radiology Detection — Database Schema
-- PostgreSQL 16 | Normalized schema with RBAC
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── ENUM Types ──────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('ADMIN', 'RADIOLOGIST', 'PHYSICIAN', 'LAB_TECH');
CREATE TYPE scan_modality AS ENUM ('XRAY', 'CT', 'MRI', 'ULTRASOUND');
CREATE TYPE scan_status AS ENUM ('UPLOADED', 'PREPROCESSING', 'ANALYZING', 'COMPLETED', 'FAILED');
CREATE TYPE report_status AS ENUM ('PENDING', 'APPROVED', 'OVERRIDDEN');

-- ─── Users Table ─────────────────────────────────────────────
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'LAB_TECH',
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Patients Table ──────────────────────────────────────────
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR(50) UNIQUE NOT NULL,  -- Hospital patient ID
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    contact_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Medical Images (Scans) Table ────────────────────────────
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES users(id),
    modality scan_modality NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    processed_path VARCHAR(500),
    file_size_bytes BIGINT,
    file_format VARCHAR(20) NOT NULL,  -- JPEG, PNG, DICOM
    status scan_status DEFAULT 'UPLOADED',
    notes TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- ─── AI Models Registry ──────────────────────────────────────
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- ResNet-50, DenseNet-121, U-Net, Custom CNN
    modality scan_modality NOT NULL,
    version VARCHAR(20) NOT NULL,
    accuracy DECIMAL(5,2),
    model_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    trained_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── AI Diagnosis Results ────────────────────────────────────
CREATE TABLE ai_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    model_id UUID REFERENCES ai_models(id),
    predicted_condition VARCHAR(255) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,  -- 0.00 to 100.00
    heatmap_path VARCHAR(500),
    inference_time_ms INTEGER,
    additional_findings JSONB,  -- Multi-label results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Diagnostic Reports ──────────────────────────────────────
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    ai_result_id UUID REFERENCES ai_results(id),
    reviewed_by UUID REFERENCES users(id),  -- Radiologist
    ai_prediction VARCHAR(255),
    final_diagnosis VARCHAR(255),
    radiologist_notes TEXT,
    status report_status DEFAULT 'PENDING',
    report_pdf_path VARCHAR(500),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Audit Log ───────────────────────────────────────────────
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Indexes ─────────────────────────────────────────────────
CREATE INDEX idx_scans_patient ON scans(patient_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_modality ON scans(modality);
CREATE INDEX idx_ai_results_scan ON ai_results(scan_id);
CREATE INDEX idx_reports_scan ON reports(scan_id);
CREATE INDEX idx_reports_reviewer ON reports(reviewed_by);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);

-- ─── Seed Data: Default AI Models ────────────────────────────
INSERT INTO ai_models (model_name, model_type, modality, version, accuracy, model_path) VALUES
    ('ChestXray-ResNet50', 'ResNet-50', 'XRAY', '1.0.0', 92.00, '/app/models/resnet50_chest.pth'),
    ('LungCT-DenseNet121', 'DenseNet-121', 'CT', '1.0.0', 89.50, '/app/models/densenet121_lung.pth'),
    ('BrainMRI-UNet', 'U-Net', 'MRI', '1.0.0', 84.00, '/app/models/unet_brain.pth'),
    ('BoneXray-CustomCNN', 'Custom CNN', 'XRAY', '1.0.0', 88.00, '/app/models/custom_cnn_bone.pth');

-- ─── Seed Data: Default Admin User ──────────────────────────
-- Password: admin123 (bcrypt hashed)
INSERT INTO users (email, password_hash, full_name, role, department) VALUES
    ('admin@radiology.ai', '$2b$12$LJ3m4ys3Lz0gHr0wGxK4/.1ZrJzYh0kqsVJHU5Dy3T5V0MHGFmSqe', 'System Administrator', 'ADMIN', 'IT'),
    ('dr.sharma@hospital.com', '$2b$12$LJ3m4ys3Lz0gHr0wGxK4/.1ZrJzYh0kqsVJHU5Dy3T5V0MHGFmSqe', 'Dr. Priya Sharma', 'RADIOLOGIST', 'Radiology'),
    ('dr.patel@hospital.com', '$2b$12$LJ3m4ys3Lz0gHr0wGxK4/.1ZrJzYh0kqsVJHU5Dy3T5V0MHGFmSqe', 'Dr. Raj Patel', 'PHYSICIAN', 'Internal Medicine'),
    ('tech.kumar@hospital.com', '$2b$12$LJ3m4ys3Lz0gHr0wGxK4/.1ZrJzYh0kqsVJHU5Dy3T5V0MHGFmSqe', 'Amit Kumar', 'LAB_TECH', 'Radiology Lab');

-- ─── Seed Data: Sample Patient ───────────────────────────────
INSERT INTO patients (patient_id, full_name, date_of_birth, gender, contact_number) VALUES
    ('PAT-2026-001', 'Rajesh Verma', '1985-03-15', 'Male', '+91-9876543210'),
    ('PAT-2026-002', 'Anita Singh', '1990-07-22', 'Female', '+91-9123456789');
