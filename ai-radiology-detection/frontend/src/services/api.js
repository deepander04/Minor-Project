import axios from 'axios';

// When VITE_API_URL is set (e.g. http://localhost:8080), use it.
// When empty/unset, use relative URLs — works with both Vite proxy and Nginx.
const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000, // 30s timeout for AI inference
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401, show connection errors
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    if (!err.response) {
      console.error('Network error — backend may not be running:', err.message);
    }
    return Promise.reject(err);
  }
);

// ─── Auth ────────────────────────────────────────────────────
export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (data) => api.post('/api/auth/register', data),
  me: () => api.get('/api/auth/me'),
  listUsers: () => api.get('/api/auth/users'),
};

// ─── Upload & Scans ─────────────────────────────────────────
export const scanAPI = {
  upload: (formData) => api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // 60s for large uploads
  }),
  list: (params) => api.get('/api/scans', { params }),
  get: (id) => api.get(`/api/scans/${id}`),
  getImage: (id) => `${API_URL}/api/scans/${id}/image`,
};

// ─── Patients ────────────────────────────────────────────────
export const patientAPI = {
  list: () => api.get('/api/patients'),
  create: (data) => api.post('/api/patients', data),
};

// ─── Preprocessing ───────────────────────────────────────────
export const preprocessAPI = {
  run: (scanId) => api.post(`/api/preprocess/${scanId}`),
  batch: () => api.post('/api/preprocess/batch'),
};

// ─── AI Inference ────────────────────────────────────────────
export const inferenceAPI = {
  analyze: (scanId) => api.post(`/api/analyze/${scanId}`),
  getResults: (scanId) => api.get(`/api/results/${scanId}`),
  getHeatmap: (resultId) => `${API_URL}/api/heatmap/${resultId}`,
  listModels: () => api.get('/api/models'),
};

// ─── Reports ─────────────────────────────────────────────────
export const reportAPI = {
  create: (data) => api.post('/api/reports', data),
  list: (params) => api.get('/api/reports', { params }),
  get: (id) => api.get(`/api/reports/${id}`),
  downloadPdf: (id) => `${API_URL}/api/reports/${id}/pdf`,
};

export default api;
