import React, { useState } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, FilePlus } from 'lucide-react';
import { motion } from 'framer-motion';

export default function UploadScreen() {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setStatus('');
            setIsSuccess(false);
        }
    };

    const handleFileUpload = async () => {
        if (!file) return;

        setLoading(true);
        setStatus('Ingesting Data Pipeline (Clean → Harmonize → Train)...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (res.ok) {
                const result = await res.json();
                setStatus(`Success! Automatically processed ${result.records_processed || 'all'} records.`);
                setIsSuccess(true);
                setFile(null);
            } else {
                const error = await res.json();
                setStatus(`Error: ${error.detail || 'Upload failed'}`);
                setIsSuccess(false);
            }
        } catch (err) {
            console.error(err);
            setStatus(`Error: ${err.message}`);
            setIsSuccess(false);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 800, margin: '0 auto', marginTop: 40 }}>
            <div className="page-header">
                <h1 className="page-title">Dataset Ingestion</h1>
                <p className="page-subtitle">Upload fragmented CSV data to unify it into standard relational databases.</p>
            </div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
                className="card glass"
                style={{ textAlign: 'center', padding: '60px 40px', border: '1px dashed var(--primary)' }}
            >
                <motion.div
                    animate={{ y: [0, -10, 0] }}
                    transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                    style={{ marginBottom: 30, color: 'var(--primary)', display: 'inline-block' }}
                >
                    <UploadCloud size={80} strokeWidth={1.5} />
                </motion.div>

                <h2 style={{ marginBottom: 16 }}>Select Dataset</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: 30 }}>Supported formats: .csv only</p>

                <div style={{ position: 'relative', overflow: 'hidden', display: 'inline-block', marginBottom: 40 }}>
                    <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--bg-card)', color: 'var(--primary)', border: '1px solid var(--primary)' }}>
                        <FilePlus size={18} />
                        {file ? file.name : "Browse Files"}
                    </button>
                    <input
                        type="file"
                        accept=".csv"
                        onChange={handleFileChange}
                        disabled={loading}
                        style={{ position: 'absolute', top: 0, left: 0, opacity: 0, width: '100%', height: '100%', cursor: 'pointer' }}
                    />
                </div>

                <div style={{ display: 'block' }}>
                    <button
                        className="btn-primary"
                        onClick={handleFileUpload}
                        disabled={!file || loading}
                        style={{ padding: '14px 40px', fontSize: 16, width: '100%', maxWidth: 300 }}
                    >
                        {loading ? 'Processing Pipeline...' : 'Upload & Proceed'}
                    </button>
                </div>

                {status && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={{
                            marginTop: 30,
                            padding: 16,
                            borderRadius: 12,
                            background: isSuccess ? 'rgba(16, 185, 129, 0.1)' : loading ? 'rgba(109, 168, 255, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            border: `1px solid ${isSuccess ? 'var(--success)' : loading ? 'var(--primary)' : 'var(--danger)'}`,
                            color: isSuccess ? 'var(--success)' : loading ? 'var(--primary)' : 'var(--danger)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 10,
                            fontWeight: 500
                        }}>
                        {isSuccess && <CheckCircle size={20} />}
                        {!isSuccess && !loading && <AlertCircle size={20} />}
                        {status}
                    </motion.div>
                )}
            </motion.div>
        </div>
    );
}
