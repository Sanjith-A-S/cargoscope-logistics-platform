/**
 * pages/UploadScreen.jsx
 *
 * Standalone upload page at /upload — reachable directly from the NavRail.
 * Never nested inside Settings; Settings may contain a shortcut link here.
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, Settings } from 'lucide-react';
import UploadPanel from '../features/upload/UploadPanel';

export default function UploadScreen() {
  return (
    <div style={{ maxWidth: 1200, paddingBottom: 60 }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Upload size={20} color="var(--accent)" strokeWidth={2.5} />
            Upload data
          </h1>
          <p className="page-subtitle">
            Upload a CSV to create or update a dataset. Required columns: shipment_id, customer,
            origin, destination, order_date — fuzzy matching is applied automatically.
          </p>
        </div>
        <Link
          to="/settings"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 13,
            color: 'var(--text-secondary)',
            textDecoration: 'none',
            padding: '6px 10px',
            borderRadius: 8,
            border: '1px solid var(--border)',
            background: 'var(--bg-surface-2)',
            flexShrink: 0,
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-surface)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-surface-2)'}
        >
          <Settings size={13} />
          Settings
        </Link>
      </div>

      <UploadPanel />
    </div>
  );
}
