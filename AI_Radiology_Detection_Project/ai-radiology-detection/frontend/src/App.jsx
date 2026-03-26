import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './utils/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import ScansPage from './pages/ScansPage';
import ScanDetailPage from './pages/ScanDetailPage';
import ReportsPage from './pages/ReportsPage';

function AppLayout({ children }) {
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected — All authenticated users */}
          <Route path="/dashboard" element={
            <ProtectedRoute><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>
          } />

          {/* Upload — Admin, Radiologist, Lab Tech */}
          <Route path="/upload" element={
            <ProtectedRoute allowedRoles={['ADMIN', 'RADIOLOGIST', 'LAB_TECH']}>
              <AppLayout><UploadPage /></AppLayout>
            </ProtectedRoute>
          } />

          {/* Scans — Admin, Radiologist, Lab Tech */}
          <Route path="/scans" element={
            <ProtectedRoute allowedRoles={['ADMIN', 'RADIOLOGIST', 'LAB_TECH']}>
              <AppLayout><ScansPage /></AppLayout>
            </ProtectedRoute>
          } />

          {/* Scan Detail — Admin, Radiologist (for review + override) */}
          <Route path="/scans/:id" element={
            <ProtectedRoute allowedRoles={['ADMIN', 'RADIOLOGIST']}>
              <AppLayout><ScanDetailPage /></AppLayout>
            </ProtectedRoute>
          } />

          {/* Reports — Admin, Radiologist, Physician */}
          <Route path="/reports" element={
            <ProtectedRoute allowedRoles={['ADMIN', 'RADIOLOGIST', 'PHYSICIAN']}>
              <AppLayout><ReportsPage /></AppLayout>
            </ProtectedRoute>
          } />

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
