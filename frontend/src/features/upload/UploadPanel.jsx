/**
 * features/upload/UploadPanel.jsx
 *
 * CSV upload with dataset selector. Allows attaching the CSV to an existing
 * dataset or creating a new one on the fly.
 */
import React, { useState, useRef } from 'react';
import api from '../../services/apiService';
import { useDataset } from '../datasets/DatasetContext';

export default function UploadPanel({ onSuccess }) {
  const { datasets, activeDataset, reload } = useDataset();
  const [file, setFile] = useState(null);
  const [targetDatasetId, setTargetDatasetId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f && f.name.endsWith('.csv')) {
      setFile(f);
      setError(null);
    } else {
      setError('Only CSV files are supported.');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f && f.name.endsWith('.csv')) {
      setFile(f);
      setError(null);
    } else {
      setError('Only CSV files are supported.');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    if (targetDatasetId) {
      formData.append('dataset_id', targetDatasetId);
    }

    try {
      const res = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
      await reload();
      if (onSuccess) onSuccess(res.data);
    } catch (e) {
      const detail = e?.response?.data;
      if (detail?.error) {
        setError(`${detail.error}\nMissing: ${(detail.missing_fields || []).join(', ')}`);
      } else {
        setError(e?.response?.data?.detail || 'Upload failed. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-panel">
      {/* Dataset target selector */}
      <div className="upload-panel__dataset-row">
        <label className="upload-panel__label">Upload into dataset</label>
        <select
          className="upload-panel__select"
          value={targetDatasetId}
          onChange={e => setTargetDatasetId(e.target.value)}
        >
          <option value="">Auto-create new dataset from file name</option>
          {datasets.map(ds => (
            <option key={ds.id} value={ds.id}>
              {ds.name} ({ds.source_row_count?.toLocaleString() ?? 0} rows)
            </option>
          ))}
        </select>
      </div>

      {/* Drop zone */}
      <div
        className={`upload-panel__dropzone${file ? ' upload-panel__dropzone--has-file' : ''}`}
        onDrop={handleDrop}
        onDragOver={e => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        {file ? (
          <div className="upload-panel__file-info">
            <span className="upload-panel__file-icon">📄</span>
            <span className="upload-panel__file-name">{file.name}</span>
            <span className="upload-panel__file-size">
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
          </div>
        ) : (
          <div className="upload-panel__placeholder">
            <span className="upload-panel__icon">☁</span>
            <p>Drop a CSV file here or <u>browse</u></p>
            <p className="upload-panel__hint">
              Required columns: shipment_id, customer, origin, destination, order_date.
              Fuzzy column matching is applied automatically.
            </p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && <div className="upload-panel__error">{error}</div>}

      {/* Result */}
      {result && (
        <div className="upload-panel__result">
          <strong>✓ Upload complete</strong>
          <ul>
            <li>{result.records_processed?.toLocaleString()} rows processed</li>
            <li>{result.records_inserted?.toLocaleString()} new rows inserted</li>
            <li>Dataset ID: {result.dataset_id}</li>
          </ul>
          {result.detected_schema && Object.keys(result.detected_schema).length > 0 && (
            <details>
              <summary>Column mapping applied</summary>
              <ul>
                {Object.entries(result.detected_schema).map(([from, to]) => (
                  <li key={from}>{from} → {to}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}

      {/* Upload button */}
      <button
        className="btn btn--primary upload-panel__btn"
        onClick={handleUpload}
        disabled={!file || uploading}
      >
        {uploading ? 'Uploading…' : 'Upload CSV'}
      </button>
    </div>
  );
}
