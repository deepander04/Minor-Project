import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { scanAPI, patientAPI, preprocessAPI, inferenceAPI } from '../services/api';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [modality, setModality] = useState('');
  const [patientId, setPatientId] = useState('');
  const [patients, setPatients] = useState([]);
  const [notes, setNotes] = useState('');
  const [status, setStatus] = useState({ step: 'idle', message: '' });
  const [error, setError] = useState('');
  const fileRef = useRef();
  const navigate = useNavigate();

  useEffect(() => {
    patientAPI.list().then((res) => setPatients(res.data.patients || [])).catch(() => {});
  }, []);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    setError('');
    if (!f) return;

    const ext = f.name.split('.').pop().toLowerCase();
    const allowed = ['jpeg', 'jpg', 'png', 'dcm', 'dicom'];
    if (!allowed.includes(ext)) {
      setError('Invalid file format. Please upload JPEG, PNG, or DICOM.');
      setFile(null);
      setPreview(null);
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setError('File exceeds maximum allowed size of 50MB.');
      setFile(null);
      setPreview(null);
      return;
    }

    setFile(f);
    if (ext !== 'dcm' && ext !== 'dicom') {
      const reader = new FileReader();
      reader.onload = (ev) => setPreview(ev.target.result);
      reader.readAsDataURL(f);
    } else {
      setPreview(null);
    }
  };

  const handleUpload = async () => {
    setError('');
    if (!file) return setError('Please select a file');
    if (!modality) return setError('Please select a scan type to proceed.');
    if (!patientId) return setError('Please select a patient');

    try {
      // Step 1: Upload
      setStatus({ step: 'uploading', message: 'Uploading image...' });
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patient_id', patientId);
      formData.append('modality', modality);
      formData.append('notes', notes);
      const uploadRes = await scanAPI.upload(formData);
      const scanId = uploadRes.data.scan.id;

      // Step 2: Preprocess
      setStatus({ step: 'preprocessing', message: 'Preprocessing image (normalization, resizing, denoising)...' });
      await preprocessAPI.run(scanId);

      // Step 3: AI Analysis
      setStatus({ step: 'analyzing', message: 'Running AI analysis (CNN inference + Grad-CAM)...' });
      await inferenceAPI.analyze(scanId);

      setStatus({ step: 'done', message: 'Analysis complete! Redirecting to results...' });
      setTimeout(() => navigate(`/scans/${scanId}`), 1500);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed');
      setStatus({ step: 'idle', message: '' });
    }
  };

  const modalities = [
    { value: 'XRAY', label: 'Chest X-ray', desc: 'Pneumonia, TB, COVID-19, Cardiomegaly', model: 'ResNet-50' },
    { value: 'CT', label: 'CT Scan', desc: 'Lung nodules, Lung cancer, Pleural effusion', model: 'DenseNet-121' },
    { value: 'MRI', label: 'Brain MRI', desc: 'Brain tumor, Stroke, Hemorrhage', model: 'U-Net' },
    { value: 'ULTRASOUND', label: 'Ultrasound', desc: 'Gallstones, Liver lesion', model: 'Custom CNN' },
  ];

  const isProcessing = status.step !== 'idle' && status.step !== 'done';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Upload Medical Image</h1>
      <p className="text-gray-500 mb-8">Upload a patient scan for AI-powered disease detection</p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">{error}</div>
      )}

      {/* Processing Status */}
      {status.step !== 'idle' && (
        <div className={`mb-6 p-4 rounded-lg border ${status.step === 'done' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-blue-50 border-blue-200 text-blue-700'}`}>
          <div className="flex items-center gap-3">
            {isProcessing && <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />}
            {status.step === 'done' && <span>✅</span>}
            <span className="font-medium">{status.message}</span>
          </div>
          {isProcessing && (
            <div className="mt-3 flex gap-2">
              {['uploading', 'preprocessing', 'analyzing'].map((s, i) => (
                <div key={s} className={`flex-1 h-2 rounded-full ${
                  ['uploading', 'preprocessing', 'analyzing'].indexOf(status.step) >= i ? 'bg-blue-500' : 'bg-blue-200'
                }`} />
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: File Upload */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">1. Select Image</h2>
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-primary-400 transition"
          >
            {preview ? (
              <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-lg" />
            ) : (
              <>
                <div className="text-4xl mb-3">🩻</div>
                <p className="text-gray-600 font-medium">Click to select image</p>
                <p className="text-xs text-gray-400 mt-1">JPEG, PNG, DICOM (max 50MB)</p>
              </>
            )}
          </div>
          <input ref={fileRef} type="file" className="hidden" accept=".jpeg,.jpg,.png,.dcm,.dicom" onChange={handleFileChange} />
          {file && <p className="mt-3 text-sm text-gray-600">Selected: <strong>{file.name}</strong> ({(file.size / 1024 / 1024).toFixed(2)} MB)</p>}

          {/* Patient Selection */}
          <div className="mt-6">
            <h2 className="font-semibold text-gray-900 mb-3">2. Select Patient</h2>
            <select value={patientId} onChange={(e) => setPatientId(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
              <option value="">-- Select Patient --</option>
              {patients.map((p) => (
                <option key={p.id} value={p.patient_id}>{p.patient_id} — {p.full_name}</option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Notes (optional)</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
              placeholder="Additional notes for the radiologist..." />
          </div>
        </div>

        {/* Right: Scan Type */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">3. Select Scan Type</h2>
          <div className="space-y-3">
            {modalities.map((m) => (
              <label key={m.value}
                className={`flex items-start gap-4 p-4 rounded-xl border-2 cursor-pointer transition ${
                  modality === m.value ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
                }`}>
                <input type="radio" name="modality" value={m.value} checked={modality === m.value}
                  onChange={(e) => setModality(e.target.value)} className="mt-1" />
                <div>
                  <p className="font-medium text-gray-900">{m.label}</p>
                  <p className="text-sm text-gray-500">{m.desc}</p>
                  <p className="text-xs text-primary-600 mt-1">Model: {m.model}</p>
                </div>
              </label>
            ))}
          </div>

          <button onClick={handleUpload} disabled={isProcessing || !file || !modality || !patientId}
            className="w-full mt-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
            {isProcessing ? 'Processing...' : 'Upload & Analyze'}
          </button>
        </div>
      </div>
    </div>
  );
}
