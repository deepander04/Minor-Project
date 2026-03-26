import { useState, useEffect } from 'react';
import { reportAPI } from '../services/api';

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [filter, setFilter] = useState('');

  useEffect(() => { loadReports(); }, [filter]);

  const loadReports = async () => {
    try {
      const params = {};
      if (filter) params.status = filter;
      const res = await reportAPI.list(params);
      setReports(res.data.reports || []);
    } catch (err) {
      console.error(err);
    }
  };

  const statusStyle = (s) => {
    const map = { PENDING: 'bg-amber-50 text-amber-700', APPROVED: 'bg-green-50 text-green-700', OVERRIDDEN: 'bg-purple-50 text-purple-700' };
    return map[s] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Diagnostic Reports</h1>
        <p className="text-gray-500">View and download diagnostic reports</p>
      </div>

      <div className="flex gap-3 mb-6">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none">
          <option value="">All Status</option>
          <option value="APPROVED">Approved</option>
          <option value="OVERRIDDEN">Overridden</option>
          <option value="PENDING">Pending</option>
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Report ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">AI Prediction</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Final Diagnosis</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">PDF</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {reports.length === 0 ? (
              <tr><td colSpan="6" className="px-6 py-12 text-center text-gray-400">No reports found</td></tr>
            ) : (
              reports.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-mono text-gray-900">{r.id?.slice(0, 8).toUpperCase()}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{r.ai_prediction || '-'}</td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{r.final_diagnosis || '-'}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyle(r.status)}`}>{r.status}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4">
                    {r.report_pdf_path ? (
                      <a href={reportAPI.downloadPdf(r.id)} target="_blank" rel="noopener noreferrer"
                        className="text-sm text-primary-600 hover:underline font-medium">
                        Download PDF
                      </a>
                    ) : (
                      <span className="text-sm text-gray-400">N/A</span>
                    )}
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
