import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { scanAPI, inferenceAPI, reportAPI } from '../services/api';

export default function ScanDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [scan, setScan] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [diagnosis, setDiagnosis] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => { loadData(); }, [id]);

  const loadData = async () => {
    try {
      const scanRes = await scanAPI.get(id);
      setScan(scanRes.data.scan);

      if (scanRes.data.scan.status === 'COMPLETED') {
        const resRes = await inferenceAPI.getResults(id);
        const r = resRes.data.results || [];
        setResults(r);
        if (r.length > 0) setDiagnosis(r[0].predicted_condition);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReport = async () => {
    if (!diagnosis) return;
    setSubmitting(true);
    try {
      await reportAPI.create({
        scan_id: id,
        final_diagnosis: diagnosis,
        notes: notes,
      });
      setSubmitted(true);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to submit report');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (!scan) return <div className="text-center py-20 text-gray-500">Scan not found</div>;

  const latestResult = results[0];
  const isRadiologist = user?.role === 'RADIOLOGIST' || user?.role === 'ADMIN';
  const token = localStorage.getItem('token');

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scan Analysis</h1>
          <p className="text-gray-500">{scan.original_filename} — {scan.modality}</p>
        </div>
        <span className={`px-3 py-1 text-sm font-medium rounded-full ${
          scan.status === 'COMPLETED' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
        }`}>{scan.status}</span>
      </div>

      {/* Side-by-Side View */}
      {scan.status === 'COMPLETED' && latestResult && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Original Image */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Original Image</h2>
              <div className="bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center min-h-[300px]">
                <img
                  src={`${scanAPI.getImage(id)}?token=${token}`}
                  alt="Original scan"
                  className="max-w-full max-h-[400px] object-contain"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              </div>
            </div>

            {/* AI Heatmap */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="font-semibold text-gray-900 mb-4">Grad-CAM Heatmap</h2>
              <div className="bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center min-h-[300px]">
                {latestResult.heatmap_path ? (
                  <img
                    src={`${inferenceAPI.getHeatmap(latestResult.id)}?token=${token}`}
                    alt="Grad-CAM heatmap"
                    className="max-w-full max-h-[400px] object-contain"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                ) : (
                  <p className="text-gray-400 text-center p-8">No heatmap generated (normal scan)</p>
                )}
              </div>
            </div>
          </div>

          {/* AI Results */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
            <h2 className="font-semibold text-gray-900 mb-4">AI Detection Results</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-500">Predicted Condition</p>
                <p className="text-lg font-bold text-gray-900 mt-1">{latestResult.predicted_condition}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Confidence Score</p>
                <div className="flex items-center gap-3 mt-1">
                  <p className="text-lg font-bold text-gray-900">{latestResult.confidence_score}%</p>
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${latestResult.confidence_score >= 90 ? 'bg-green-500' : latestResult.confidence_score >= 80 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${latestResult.confidence_score}%` }}
                    />
                  </div>
                </div>
                {latestResult.confidence_score < 80 && (
                  <p className="text-xs text-amber-600 mt-1">⚠️ Low confidence — manual review strongly recommended</p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-500">Inference Time</p>
                <p className="text-lg font-bold text-gray-900 mt-1">{latestResult.inference_time_ms}ms</p>
              </div>
            </div>

            {/* Multi-label scores */}
            {latestResult.additional_findings && (
              <div className="mt-6 pt-4 border-t border-gray-100">
                <p className="text-sm font-medium text-gray-700 mb-3">All Detected Probabilities:</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {Object.entries(latestResult.additional_findings).map(([disease, score]) => (
                    <div key={disease} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">{disease}</p>
                      <p className="font-semibold text-gray-900">{score}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Radiologist Review Panel */}
          {isRadiologist && !submitted && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
              <h2 className="font-semibold text-gray-900 mb-4">Radiologist Final Diagnosis</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Final Diagnosis</label>
                  <select value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                    <option value="">-- Select Diagnosis --</option>
                    {latestResult.additional_findings && Object.keys(latestResult.additional_findings).map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                    <option value="Other">Other (specify in notes)</option>
                  </select>
                  {diagnosis && diagnosis !== latestResult.predicted_condition && (
                    <p className="text-xs text-amber-600 mt-1">⚠️ Your diagnosis differs from the AI prediction — this will be logged as an OVERRIDE</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Notes</label>
                  <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                    placeholder="Add clinical observations, reasoning for override, etc." />
                </div>
                <button onClick={handleSubmitReport} disabled={submitting || !diagnosis}
                  className="px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50">
                  {submitting ? 'Submitting...' : 'Submit Final Diagnosis & Generate Report'}
                </button>
              </div>
            </div>
          )}

          {submitted && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center mb-8">
              <p className="text-green-700 font-semibold text-lg">Report submitted successfully!</p>
              <p className="text-green-600 text-sm mt-1">PDF report has been generated and stored.</p>
              <button onClick={() => navigate('/reports')}
                className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition">
                View Reports
              </button>
            </div>
          )}
        </>
      )}

      {/* Scan Info */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Scan Information</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div><span className="text-gray-500">Modality:</span><br/><strong>{scan.modality}</strong></div>
          <div><span className="text-gray-500">Format:</span><br/><strong>{scan.file_format}</strong></div>
          <div><span className="text-gray-500">Size:</span><br/><strong>{scan.file_size_bytes ? `${(scan.file_size_bytes/1024/1024).toFixed(2)} MB` : '-'}</strong></div>
          <div><span className="text-gray-500">Uploaded:</span><br/><strong>{scan.uploaded_at ? new Date(scan.uploaded_at).toLocaleString() : '-'}</strong></div>
        </div>
      </div>
    </div>
  );
}
