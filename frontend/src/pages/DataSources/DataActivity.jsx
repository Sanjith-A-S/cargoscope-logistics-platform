import React, { useState, useEffect } from 'react';
import { Activity, FileText, Cpu, CheckCircle, AlertTriangle, Database, ShieldCheck, Globe, Mail, Upload } from 'lucide-react';
import { apiService } from '../../services/apiService';
import { useNavigate } from 'react-router-dom';

const DataActivity = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading]       = useState(true);
  const navigate                    = useNavigate();

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await apiService.getPipelineLogs(50);
        if (data && data.logs) setActivities(data.logs);
      } catch (error) {
        console.error('Failed to fetch pipeline logs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, []);

  const getIcon = (type) => {
    const t = type.toLowerCase();
    if (t.includes('api') || t.includes('connection')) return <Cpu size={15} />;
    if (t.includes('doc') || t.includes('parsing') || t.includes('extraction')) return <FileText size={15} />;
    if (t.includes('email') || t.includes('scan')) return <Mail size={15} />;
    if (t.includes('success') || t.includes('ingestion')) return <CheckCircle size={15} />;
    if (t.includes('error')) return <AlertTriangle size={15} />;
    return <Activity size={15} />;
  };

  const getIconStyle = (type) => {
    const t = type.toLowerCase();
    if (t.includes('error'))   return { color: 'var(--color-delayed-text)', background: 'var(--color-delayed-bg)' };
    if (t.includes('warning')) return { color: 'var(--color-atrisk-text)',  background: 'var(--color-atrisk-bg)' };
    if (t.includes('success') || t.includes('ingestion'))
      return { color: 'var(--color-ontime-text)', background: 'var(--color-ontime-bg)' };
    return { color: 'var(--accent)', background: 'var(--accent-subtle)' };
  };

  const formatTime = (isoString) => {
    const date    = new Date(isoString + 'Z');
    const now     = new Date();
    const diffMs  = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1)  return 'just now';
    if (diffMin < 60) return `${diffMin} min ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24)  return `${diffHr} hr ago`;
    return date.toLocaleDateString();
  };

  const errorCount   = activities.filter(a => a.event_type.toLowerCase().includes('error')).length;
  const successCount = activities.filter(a => !a.event_type.toLowerCase().includes('error')).length;
  const successRate  = activities.length > 0
    ? `${((successCount / activities.length) * 100).toFixed(1)}%`
    : '—';

  return (
    <div style={{ maxWidth: 1000, paddingBottom: 60 }}>
      {/* ── Header ── */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Upload data</h1>
          <p className="page-subtitle">Pipeline activity and system health.</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => navigate('/upload')}
          style={{ flexShrink: 0 }}
        >
          <Upload size={15} />
          Upload CSV
        </button>
      </div>

      {/* ── Stat strip ── */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 28 }}>
        {[
          { label: 'Log entries',   value: loading ? '…' : String(activities.length) },
          { label: 'Status',        value: loading ? 'Syncing' : 'Active' },
          { label: 'Success rate',  value: loading ? '…' : successRate },
          { label: 'Errors',        value: loading ? '…' : String(errorCount), valueClass: errorCount > 0 ? 'status-delayed' : '' },
        ].map((m, i) => (
          <div key={i} className="kpi-card">
            <div className="kpi-label">{m.label}</div>
            <div className={`kpi-value ${m.valueClass || ''}`} style={{ fontSize: 24 }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* ── Main content ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20, alignItems: 'start' }}>

        {/* Activity log */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 7 }}>
              <Activity size={16} color="var(--accent)" /> Ingestion log
            </h3>
            {loading && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Refreshing…</span>}
          </div>

          <div style={{ maxHeight: 520, overflowY: 'auto' }}>
            {!loading && activities.length === 0 && (
              <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
                Nothing here yet — upload a CSV to get started.
              </div>
            )}
            {activities.map((act, i) => {
              const iconStyle = getIconStyle(act.event_type);
              return (
                <div key={i} style={{
                  padding: '14px 20px',
                  borderBottom: i < activities.length - 1 ? '1px solid var(--border)' : 'none',
                  display: 'flex', gap: 14, alignItems: 'flex-start',
                  background: i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-surface-2)',
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: iconStyle.background,
                    color: iconStyle.color,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    {getIcon(act.event_type)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8, marginBottom: 3 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {act.event_type}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', flexShrink: 0 }}>
                        {formatTime(act.timestamp)}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                      {act.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Source health sidebar */}
        <div className="card">
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: 0.3, marginBottom: 16 }}>
            Source health
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { icon: Mail,       label: 'Inbox monitor',  status: 'Connected', note: 'Ready for sync' },
              { icon: Cpu,        label: 'Carrier APIs',   status: 'Connected', note: 'Active polling' },
              { icon: Globe,      label: 'Webhooks',       status: 'Listening', note: 'Endpoint online' },
            ].map((src, i) => (
              <div key={i} style={{
                padding: '10px 12px',
                background: 'var(--bg-surface-2)',
                borderRadius: 8,
                border: '1px solid var(--border)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <src.icon size={13} color="var(--text-secondary)" /> {src.label}
                  </span>
                  <span className="badge badge-ontime">{src.status}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{src.note}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataActivity;
