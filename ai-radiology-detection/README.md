# AI-Powered Radiology Detection

A microservices-based deep learning platform that analyzes medical images (X-ray, CT, MRI) to detect diseases, highlight suspicious regions with Grad-CAM heatmaps, and support radiologist clinical workflow.

**Course:** 21CSP302L Minor Project | SRM Institute of Science and Technology | Review 2, March 2026

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite + Tailwind CSS | SPA with role-based UI |
| **API Gateway** | Nginx | Request routing, rate limiting, SSL termination |
| **Auth Service** | Flask + PyJWT + bcrypt | JWT authentication, RBAC |
| **Upload Service** | Flask + werkzeug | Image upload, validation (JPEG/PNG/DICOM, ≤50MB) |
| **Preprocessing Service** | Flask + OpenCV + NumPy | Normalization, CLAHE, resizing (224×224 / 256×256), denoising |
| **AI Inference Service** | Flask + OpenCV (PyTorch in production) | CNN inference (ResNet-50/DenseNet-121/U-Net), Grad-CAM heatmaps |
| **Report Service** | Flask + ReportLab | PDF diagnostic report generation |
| **Database** | PostgreSQL 16 + SQLAlchemy ORM | Patient records, scan metadata, AI results, audit log |
| **Message Queue** | Redis 7 | Async job queue for preprocessing pipeline |
| **Containerization** | Docker + Docker Compose | All services containerized |
| **Deployment** | AWS (EC2, S3, RDS, ECS/K8s) | Cloud-native architecture |

---

## Architecture

```
                    ┌──────────────┐
                    │   React SPA  │  (Port 3000)
                    │  (Frontend)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Nginx Gateway│  (Port 8080)
                    │  /api/auth   │
                    │  /api/upload │
                    │  /api/analyze│
                    └──────┬───────┘
           ┌───────────────┼───────────────┐──────────────┐
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌────▼─────┐
    │Auth Service │ │Upload Svc   │ │Preprocess   │ │Inference │
    │ (5001)      │ │ (5002)      │ │ (5003)      │ │ (5004)   │
    │ JWT + RBAC  │ │ S3/Disk     │ │ OpenCV      │ │ CNN+CAM  │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └────┬─────┘
           │               │               │              │
           └───────────────┴───────┬───────┴──────────────┘
                            ┌──────▼──────┐     ┌──────────┐
                            │ PostgreSQL  │     │Report Svc│
                            │   (5432)    │     │  (5005)  │
                            └─────────────┘     │ PDF Gen  │
                                                └──────────┘
```

### Microservices Breakdown

| Service | Port | Responsibility |
|---------|------|---------------|
| **API Gateway** (Nginx) | 8080 | Routes requests, rate limiting, CORS |
| **Auth Service** | 5001 | Login, register, JWT tokens, RBAC enforcement |
| **Upload Service** | 5002 | Image upload + validation, patient/scan CRUD |
| **Preprocessing Service** | 5003 | CLAHE, normalization, resize, denoise |
| **AI Inference Service** | 5004 | CNN model inference, Grad-CAM heatmap generation |
| **Report Service** | 5005 | PDF report generation, radiologist review |
| **PostgreSQL** | 5432 | Relational database |
| **Redis** | 6379 | Message queue / caching |

---

## Database Schema

**Core Tables:** `users`, `patients`, `scans`, `ai_models`, `ai_results`, `reports`, `audit_log`

**Enums:** `user_role` (ADMIN, RADIOLOGIST, PHYSICIAN, LAB_TECH), `scan_modality` (XRAY, CT, MRI, ULTRASOUND), `scan_status`, `report_status`

---

## RBAC (Role-Based Access Control)

| Role | Upload | View AI Results | Review & Override | Generate Report | User Mgmt |
|------|--------|----------------|-------------------|-----------------|-----------|
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| Radiologist | ✅ | ✅ | ✅ | ✅ | ❌ |
| Physician | ❌ | ✅ (own patients) | ❌ | View Only | ❌ |
| Lab Technician | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## AI Models

| Imaging Modality | Model | Diseases Detected | Input Size |
|-----------------|-------|-------------------|------------|
| Chest X-ray | ResNet-50 | Pneumonia, TB, COVID-19, Cardiomegaly | 224×224 |
| CT Scan | DenseNet-121 | Lung nodules, Lung cancer, Pleural effusion | 224×224 |
| Brain MRI | U-Net | Brain tumor, Stroke, Hemorrhage | 256×256 |
| Bone X-ray | Custom CNN | Fractures, Micro-fractures | 224×224 |

> **Note:** The inference service includes a simulation layer for demo purposes. In production, replace with actual PyTorch model loading (`torch.load()`) and real Grad-CAM computation.

---

## How to Run

### Prerequisites

- Docker & Docker Compose (v2+)
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Option 1: Docker Compose (Recommended — runs everything)

```bash
# Clone the project
cd ai-radiology-detection

# Start all services
docker-compose up --build

# Access:
#   Frontend:     http://localhost:3000
#   API Gateway:  http://localhost:8080
#   Auth API:     http://localhost:5001
#   Upload API:   http://localhost:5002
```

### Option 2: Run Locally (Development)

#### 1. Start PostgreSQL and Redis

```bash
docker-compose up postgres redis -d
```

#### 2. Start Backend Services (each in a separate terminal)

```bash
cd backend

# Install dependencies (do once)
pip install flask flask-cors sqlalchemy psycopg2-binary PyJWT bcrypt opencv-python-headless numpy reportlab

# Auth Service
python auth_service/app.py

# Upload Service
python upload_service/app.py

# Preprocessing Service
python preprocessing_service/app.py

# Inference Service
python inference_service/app.py

# Report Service
python report_service/app.py
```

#### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### Default Login Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@radiology.ai | admin123 |
| Radiologist | dr.sharma@hospital.com | admin123 |
| Physician | dr.patel@hospital.com | admin123 |
| Lab Tech | tech.kumar@hospital.com | admin123 |

---

## API Endpoints

### Auth Service (`/api/auth`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login, get JWT | No |
| GET | `/api/auth/me` | Get current user | JWT |
| GET | `/api/auth/users` | List users | ADMIN |

### Upload Service (`/api/upload`, `/api/scans`, `/api/patients`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/upload` | Upload medical image | ADMIN, RADIOLOGIST, LAB_TECH |
| GET | `/api/scans` | List scans (filterable) | JWT |
| GET | `/api/scans/:id` | Get scan details | JWT |
| GET | `/api/scans/:id/image` | Serve original image | JWT |
| GET | `/api/patients` | List patients | JWT |
| POST | `/api/patients` | Create patient | ADMIN, RADIOLOGIST, LAB_TECH |

### Preprocessing Service (`/api/preprocess`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/preprocess/:scanId` | Preprocess single scan | ADMIN, RADIOLOGIST, LAB_TECH |
| POST | `/api/preprocess/batch` | Preprocess all pending | ADMIN, RADIOLOGIST |

### AI Inference Service (`/api/analyze`, `/api/results`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/analyze/:scanId` | Run AI inference | ADMIN, RADIOLOGIST |
| GET | `/api/results/:scanId` | Get AI results | ADMIN, RADIOLOGIST, PHYSICIAN |
| GET | `/api/heatmap/:resultId` | Serve heatmap image | ADMIN, RADIOLOGIST, PHYSICIAN |
| GET | `/api/models` | List AI models | JWT |

### Report Service (`/api/reports`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/reports` | Create report (submit diagnosis) | ADMIN, RADIOLOGIST |
| GET | `/api/reports` | List reports | ADMIN, RADIOLOGIST, PHYSICIAN |
| GET | `/api/reports/:id` | Get report details | ADMIN, RADIOLOGIST, PHYSICIAN |
| GET | `/api/reports/:id/pdf` | Download PDF | ADMIN, RADIOLOGIST, PHYSICIAN |

---

## Demo Workflow

1. **Login** as Lab Technician (`tech.kumar@hospital.com`)
2. **Upload** a chest X-ray image → select patient → select "Chest X-ray" modality
3. System runs: Upload → Preprocess → AI Inference automatically
4. **Login** as Radiologist (`dr.sharma@hospital.com`)
5. Go to **Scans** → open the completed scan
6. View **side-by-side** original image + Grad-CAM heatmap
7. See confidence score (e.g., "91% Pneumonia")
8. **Override** AI prediction if needed → add clinical notes → submit
9. PDF report auto-generated
10. **Login** as Physician (`dr.patel@hospital.com`)
11. Go to **Reports** → view/download the PDF
12. Try accessing AI results page as Lab Tech → **Access Denied** (RBAC working)

---

## Project Structure

```
ai-radiology-detection/
├── docker-compose.yml          # Orchestrates all services
├── nginx/
│   └── nginx.conf              # API Gateway config
├── scripts/
│   └── init_db.sql             # Database schema + seed data
├── backend/
│   ├── config/
│   │   └── settings.py         # Shared configuration
│   ├── database/
│   │   └── models.py           # SQLAlchemy ORM models
│   ├── utils/
│   │   └── auth.py             # JWT + RBAC decorators
│   ├── auth_service/
│   │   ├── app.py              # Auth endpoints
│   │   └── Dockerfile
│   ├── upload_service/
│   │   ├── app.py              # Upload + scan CRUD
│   │   └── Dockerfile
│   ├── preprocessing_service/
│   │   ├── app.py              # OpenCV pipeline
│   │   └── Dockerfile
│   ├── inference_service/
│   │   ├── app.py              # CNN inference + Grad-CAM
│   │   └── Dockerfile
│   └── report_service/
│       ├── app.py              # PDF generation
│       └── Dockerfile
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx             # Router + RBAC routes
        ├── services/
        │   └── api.js          # Axios API layer
        ├── utils/
        │   └── AuthContext.jsx  # Auth state management
        ├── components/
        │   ├── Navbar.jsx      # Role-based navigation
        │   └── ProtectedRoute.jsx
        └── pages/
            ├── LoginPage.jsx
            ├── RegisterPage.jsx
            ├── DashboardPage.jsx
            ├── UploadPage.jsx
            ├── ScansPage.jsx
            ├── ScanDetailPage.jsx  # Side-by-side heatmap view
            └── ReportsPage.jsx
```

---

## Ethics & Compliance

- **Decision-Support Only**: AI assists radiologists — never replaces them
- **HIPAA-Aware Design**: Encrypted transmission (TLS), access logs, role isolation
- **Explainability**: Grad-CAM heatmaps show WHY the AI flagged a region
- **Audit Trail**: Both AI prediction and radiologist's final decision are logged
- **Algorithmic Bias Awareness**: Designed for diverse, representative datasets

---

## Future Enhancements

- Vision Transformers (Swin Transformer) for improved accuracy
- Federated Learning for multi-hospital training without data sharing
- Multi-modal fusion (image + clinical notes via NLP)
- Real-time PACS integration via DICOM protocol
- MedSAM foundation model fine-tuning
- Uncertainty quantification (Monte Carlo Dropout)
