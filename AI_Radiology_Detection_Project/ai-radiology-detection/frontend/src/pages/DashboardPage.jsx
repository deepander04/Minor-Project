import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { scanAPI, reportAPI, inferenceAPI } from '../services/api';

function StatCard({ label, value, color, icon }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center text-xl`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ scans: 0, completed: 0, reports: 0, pending: 0 });
  const [recentScans, setRecentScans] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [scansRes, completedRes, reportsRes] = await Promise.allSettled([
        scanAPI.list({}),
        scanAPI.list({ status: 'COMPLETED' }),
        reportAPI.list({}),
      ]);

      const allScans = scansRes.status === 'fulfilled' ? scansRes.value.data.scans : [];
      const completed = completedRes.status === 'fulfilled' ? completedRes.value.data.scans : [];
      const reports = reportsRes.status === 'fulfilled' ? reportsRes.value.data.reports : [];

      setStats({
        scans: allScans.length,
        completed: completed.length,
        reports: reports.length,
        pending: allScans.filter((s) => s.status === 'UPLOADED' || s.status === 'ANALYZING').length,
      });
      setRecentScans(allScans.slice(0, 5));
    } catch (err) {
      console.error('Dashboard load error:', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Welcome, {user?.full_name}</h1>
        <p className="text-gray-500 mt-1">AI-Powered Radiology Detection — {user?.role.replace('_', ' ')} Dashboard</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard label="Total Scans" value={stats.scans} color="bg-blue-50 text-blue-600" icon="🩻" />
        <StatCard label="AI Completed" value={stats.completed} color="bg-green-50 text-green-600" icon="✅" />
        <StatCard label="Reports" value={stats.reports} color="bg-purple-50 text-purple-600" icon="📄" />
        <StatCard label="Pending Review" value={stats.pending} color="bg-amber-50 text-amber-600" icon="⏳" />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {(user?.role === 'ADMIN' || user?.role === 'RADIOLOGIST' || user?.role === 'LAB_TECH') && (
          <Link to="/upload" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition group">
            <div className="text-3xl mb-3">📤</div>
            <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition">Upload Scan</h3>
            <p className="text-sm text-gray-500 mt-1">Upload a new medical image for AI analysis</p>
          </Link>
        )}
        {(user?.role === 'ADMIN' || user?.role === 'RADIOLOGIST') && (
          <Link to="/scans" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition group">
            <div className="text-3xl mb-3">🔬</div>
            <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition">Review Scans</h3>
            <p className="text-sm text-gray-500 mt-1">View AI results and submit diagnoses</p>
          </Link>
        )}
        <Link to="/reports" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition group">
          <div className="text-3xl mb-3">📋</div>
          <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition">View Reports</h3>
          <p className="text-sm text-gray-500 mt-1">Access diagnostic reports and PDF downloads</p>
        </Link>
      </div>

      {/* Recent Scans Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Recent Scans</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">File</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Modality</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uploaded</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {recentScans.length === 0 ? (
                <tr><td colSpan="4" className="px-6 py-8 text-center text-gray-400">No scans yet. Upload your first image.</td></tr>
              ) : (
                recentScans.map((scan) => (
                  <tr key={scan.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{scan.original_filename}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-50 text-blue-700">{scan.modality}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        scan.status === 'COMPLETED' ? 'bg-green-50 text-green-700' :
                        scan.status === 'FAILED' ? 'bg-red-50 text-red-700' :
                        'bg-amber-50 text-amber-700'
                      }`}>{scan.status}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {scan.uploaded_at ? new Date(scan.uploaded_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
