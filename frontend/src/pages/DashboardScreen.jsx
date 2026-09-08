import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/apiService';
import { useDataset } from '../features/datasets/DatasetContext';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell
} from 'recharts';
import { Package, Truck, DollarSign, Activity, AlertTriangle, ChevronRight } from 'lucide-react';

// ─── Quiet stat card — color only on the number when it's a status ────────────
const StatCard = ({ label, value, valueClass }) => (
  <div className="kpi-card">
    <div className="kpi-label">{label}</div>
    <div className={`kpi-value ${valueClass || ''}`}>{value}</div>
  </div>
);

// ─── Insight item — in the highlights panel ───────────────────────────────────
const HighlightItem = ({ icon: Icon, tone, text }) => {
  const toneColor = {
    warning: 'var(--color-atrisk-text)',
    error:   'var(--color-delayed-text)',
    success: 'var(--color-ontime-text)',
    info:    'var(--text-secondary)',
  }[tone] || 'var(--text-secondary)';

  return (
    <div style={{
      display: 'flex',
      gap: 10,
      padding: '13px 0',
      borderBottom: '1px solid var(--border)',
    }}>
      <div style={{ color: toneColor, marginTop: 1, flexShrink: 0 }}>
        <Icon size={16} />
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.55 }}>{text}</p>
    </div>
  );
};

// ─── Empty state ──────────────────────────────────────────────────────────────
const EmptyDashboard = () => {
  const navigate = useNavigate();
  return (
    <div className="empty-state" style={{ height: 420 }}>
      <Package size={40} className="empty-state-icon" />
      <h3>Nothing here yet</h3>
      <p>Upload a trade dataset CSV to populate the dashboard and start tracking shipments.</p>
      <button
        className="btn-primary"
        onClick={() => navigate('/sources/monitor')}
        style={{ marginTop: 8 }}
      >
        Upload data
      </button>
    </div>
  );
};

// ─── Dashboard ────────────────────────────────────────────────────────────────
export default function DashboardScreen() {
  const { activeDataset } = useDataset();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!activeDataset) {
      setLoading(false);
      setData(null);
      return;
    }
    loadDashboard();
  }, [activeDataset?.id]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const response = await apiService.getDashboard(activeDataset.id);
      setData(response.data);
    } catch (e) {
      console.error(e);
      if (e?.response?.status === 409) {
        setData(null);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-row">
        <div className="pulse-dot" />
        Loading…
      </div>
    );
  }

  const isEmpty = !data || (data.kpis?.total_shipments === 0);
  if (isEmpty) return <EmptyDashboard />;

  const { kpis, charts } = data;
  const dynamicInsights   = data.insights || [];

  const delayData = [
    { name: 'On time',  value: kpis.total_shipments - kpis.delayed_shipments },
    { name: 'Delayed',  value: kpis.delayed_shipments },
  ];
  const PIE_COLORS = ['var(--color-ontime-text)', 'var(--color-delayed-text)'];

  const trendData = charts.shipment_volume_trend || [];

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Overview</h1>
        <p className="page-subtitle">
          Shipment volume, carrier performance, and open anomalies at a glance.
        </p>
      </div>

      {/* ── KPI strip ── */}
      <div className="kpi-grid">
        <StatCard
          label="Total shipments"
          value={kpis.total_shipments.toLocaleString()}
        />
        <StatCard
          label="Delayed shipments"
          value={kpis.delayed_shipments.toLocaleString()}
          valueClass={kpis.delayed_shipments > 0 ? 'status-delayed' : ''}
        />
        <StatCard
          label="Average cost"
          value={`$${kpis.average_cost.toLocaleString()}`}
        />
        <StatCard
          label="Active routes"
          value={kpis.active_routes.toLocaleString()}
        />
      </div>

      {/* ── Charts row 1 ── */}
      <div className="charts-grid" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="chart-title">Shipment volume</div>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }}
                  itemStyle={{ color: 'var(--accent)' }}
                />
                <Line
                  type="monotone"
                  dataKey="volume"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: 'var(--accent)', strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="chart-title">Highlights</div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            {dynamicInsights.length > 0 ? dynamicInsights.slice(0, 4).map((insight, idx) => (
              <HighlightItem
                key={idx}
                icon={
                  insight.type === 'error' || insight.type === 'warning'
                    ? AlertTriangle
                    : insight.type === 'success' ? Truck : Activity
                }
                tone={insight.type}
                text={<span><strong>{insight.title}:</strong> {insight.message}</span>}
              />
            )) : (
              <p style={{ fontSize: 13, color: 'var(--text-muted)', padding: '12px 0' }}>
                No highlights yet — upload data to see patterns.
              </p>
            )}
          </div>
          {dynamicInsights.length > 4 && (
            <button
              style={{
                background: 'transparent', border: 'none',
                color: 'var(--accent)', cursor: 'pointer',
                textAlign: 'left', fontWeight: 500, fontSize: 13,
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '12px 0 0', fontFamily: 'inherit',
              }}
            >
              View all <ChevronRight size={14} />
            </button>
          )}
        </div>
      </div>

      {/* ── Charts row 2 ── */}
      <div className="charts-grid">
        <div className="card">
          <div className="chart-title">Carrier on-time rate</div>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.partner_performance || []} margin={{ top: 8, right: 8, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="carrier" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                <RechartsTooltip
                  cursor={{ fill: 'var(--bg-surface-2)' }}
                  contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="on_time_rate" fill="var(--accent)" name="On-time rate (%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="chart-title">Delays overview</div>
          <div style={{ width: '100%', height: 280, position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={delayData}
                  cx="50%" cy="50%"
                  innerRadius={56} outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                  stroke="none"
                >
                  {delayData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip
                  contentStyle={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Donut center label */}
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              pointerEvents: 'none',
            }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>
                {kpis.total_shipments > 0
                  ? `${((kpis.delayed_shipments / kpis.total_shipments) * 100).toFixed(1)}%`
                  : '—'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>delay rate</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
