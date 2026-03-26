import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scanAPI } from '../services/api';

export default function ScansPage() {
  const [scans, setScans] = useState([]);
  const [filter, setFilter] = useState({ status: '', modality: '' });

  useEffect(() => { loadScans(); }, [filter]);

  const loadScans = async () => {
    try {
      const params = {};
      if (filter.status) params.status = filter.status;
      if (filter.modality) params.modality = filter.modality;
      const res = await scanAPI.list(params);
      setScans(res.data.scans || []);
    } catch (err) {
      console.error(err);
    }
  };

  const statusColor = (s) => {
    const map = { UPLOADED: 'bg-gray-100 text-gray-700', PREPROCESSING: 'bg-yellow-50 text-yellow-700', ANALYZING: 'bg-blue-50 text-blue-700', COMPLETED: 'bg-green-50 text-green-700', FAILED: 'bg-red-50 text-red-700' };
    return map[s] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scans</h1>
          <p className="text-gray-500">All uploaded medical scans</p>
        </div>
        <Link to="/upload" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition">
          + Upload New
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <select value={filter.status} onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none">
          <option value="">All Status</option>
          <option value="UPLOADED">Uploaded</option>
          <option value="ANALYZING">Analyzing</option>
          <option value="COMPLETED">Completed</option>
          <option value="FAILED">Failed</option>
        </select>
        <select value={filter.modality} onChange={(e) => setFilter({ ...filter, modality: e.target.value })}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none">
          <option value="">All Modalities</option>
          <option value="XRAY">X-ray</option>
          <option value="CT">CT Scan</option>
          <option value="MRI">MRI</option>
          <option value="ULTRASOUND">Ultrasound</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">File</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Modality</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uploaded</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {scans.length === 0 ? (
              <tr><td colSpan="6" className="px-6 py-12 text-center text-gray-400">No scans found</td></tr>
            ) : (
              scans.map((scan) => (
                <tr key={scan.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{scan.original_filename}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-50 text-blue-700">{scan.modality}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColor(scan.status)}`}>{scan.status}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {scan.file_size_bytes ? `${(scan.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {scan.uploaded_at ? new Date(scan.uploaded_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <Link to={`/scans/${scan.id}`} className="text-sm text-primary-600 hover:underline">
                      {scan.status === 'COMPLETED' ? 'View Results' : 'Details'}
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
