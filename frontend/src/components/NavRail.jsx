import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  Package,
  Truck,
  Lightbulb,
  Settings,
  LogOut,
  Sun,
  Moon,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../App';
import DatasetSwitcher from '../features/datasets/DatasetSwitcher';

// ─── Nav destinations ─────────────────────────────────────────────────────────
const PRIMARY_ITEMS = [
  { to: '/',                 icon: AlertTriangle,   label: 'Risk Queue',   exact: true },
  { to: '/dashboard',        icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload',           icon: Upload,          label: 'Upload data' },
  { to: '/shipments',        icon: Package,         label: 'Shipments' },
  { to: '/carriers',         icon: Truck,           label: 'Carriers' },
  { to: '/anomalies',        icon: Lightbulb,       label: 'Insights' },
];

// ─── Individual nav item ──────────────────────────────────────────────────────
function NavItem({ to, icon: Icon, label, expanded, onClick, exact }) {
  const location = useLocation();
  const isActive = (to === '/' || exact)
    ? location.pathname === to
    : location.pathname.startsWith(to);

  return (
    <Link
      to={to}
      onClick={onClick}
      title={!expanded ? label : undefined}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: expanded ? 10 : 0,
        padding: '10px 14px',
        borderRadius: 10,
        textDecoration: 'none',
        color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
        background: isActive ? 'var(--accent-subtle)' : 'transparent',
        transition: 'background 0.15s ease, color 0.15s ease',
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        minWidth: 0,
      }}
      onMouseEnter={e => {
        if (!isActive) e.currentTarget.style.background = 'var(--bg-surface-2)';
      }}
      onMouseLeave={e => {
        if (!isActive) e.currentTarget.style.background = 'transparent';
      }}
    >
      <Icon size={18} strokeWidth={isActive ? 2.5 : 2} style={{ flexShrink: 0 }} />
      <span style={{
        fontSize: 13,
        fontWeight: isActive ? 600 : 500,
        opacity: expanded ? 1 : 0,
        transform: expanded ? 'translateX(0)' : 'translateX(-4px)',
        transition: 'opacity 0.18s ease, transform 0.18s ease',
        pointerEvents: 'none',
        fontFamily: 'inherit',
      }}>
        {label}
      </span>
    </Link>
  );
}

// ─── Icon-only action button (logout, theme) ──────────────────────────────────
function RailAction({ icon: Icon, label, onClick, expanded, danger }) {
  return (
    <button
      onClick={onClick}
      title={!expanded ? label : undefined}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: expanded ? 10 : 0,
        padding: '10px 14px',
        borderRadius: 10,
        background: 'transparent',
        border: 'none',
        cursor: 'pointer',
        color: danger ? 'var(--color-delayed-text)' : 'var(--text-secondary)',
        width: '100%',
        textAlign: 'left',
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        fontFamily: 'inherit',
        transition: 'background 0.15s ease, color 0.15s ease',
      }}
      onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-surface-2)'; }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
    >
      <Icon size={18} strokeWidth={2} style={{ flexShrink: 0 }} />
      <span style={{
        fontSize: 13,
        fontWeight: 500,
        opacity: expanded ? 1 : 0,
        transform: expanded ? 'translateX(0)' : 'translateX(-4px)',
        transition: 'opacity 0.18s ease, transform 0.18s ease',
        pointerEvents: 'none',
      }}>
        {label}
      </span>
    </button>
  );
}

// ─── NavRail ──────────────────────────────────────────────────────────────────
export default function NavRail({ theme, onToggleTheme }) {
  const [expanded, setExpanded] = useState(false);
  const railRef = useRef(null);
  const { logout } = useAuth();

  // Detect pointer capability for hover-to-expand vs tap-to-toggle
  const isPointerDevice = typeof window !== 'undefined' &&
    window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  // Click-outside collapse
  useEffect(() => {
    if (!expanded) return;
    const handler = (e) => {
      if (railRef.current && !railRef.current.contains(e.target)) {
        setExpanded(false);
      }
    };
    document.addEventListener('mousedown', handler);
    document.addEventListener('touchstart', handler);
    return () => {
      document.removeEventListener('mousedown', handler);
      document.removeEventListener('touchstart', handler);
    };
  }, [expanded]);

  const handleItemClick = () => setExpanded(false);

  const hoverProps = isPointerDevice ? {
    onMouseEnter: () => setExpanded(true),
    onMouseLeave: () => setExpanded(false),
  } : {
    onClick: (e) => {
      // Only toggle if clicking the rail itself, not a child link
      if (e.target === railRef.current) setExpanded(prev => !prev);
    },
  };

  return (
    <div
      ref={railRef}
      {...hoverProps}
      style={{
        position: 'fixed',
        left: 'var(--rail-margin)',
        top: '50%',
        transform: 'translateY(-50%)',
        zIndex: 100,
        width: expanded ? 'var(--rail-expanded)' : 'var(--rail-collapsed)',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: expanded ? 20 : 28,
        display: 'flex',
        flexDirection: 'column',
        padding: '12px 8px',
        gap: 2,
        transition: 'width 220ms cubic-bezier(0.2, 0, 0, 1), border-radius 220ms cubic-bezier(0.2, 0, 0, 1)',
        overflow: 'hidden',
        /* no box-shadow — flat, consistent with the surface system */
      }}
    >
      {/* Primary items */}
      {PRIMARY_ITEMS.map(item => (
        <NavItem
          key={item.to}
          to={item.to}
          icon={item.icon}
          label={item.label}
          expanded={expanded}
          onClick={handleItemClick}
          exact={item.exact}
        />
      ))}

      {/* Dataset switcher — only visible when rail is expanded */}
      {expanded && (
        <div style={{ padding: '4px 6px', overflow: 'hidden' }}>
          <DatasetSwitcher />
        </div>
      )}

      {/* Divider */}
      <div style={{
        height: 1,
        background: 'var(--border)',
        margin: '6px 6px',
        flexShrink: 0,
      }} />

      {/* Settings */}
      <NavItem
        to="/settings"
        icon={Settings}
        label="Settings"
        expanded={expanded}
        onClick={handleItemClick}
      />

      {/* Theme toggle */}
      <RailAction
        icon={theme === 'dark' ? Sun : Moon}
        label={theme === 'dark' ? 'Light mode' : 'Dark mode'}
        onClick={onToggleTheme}
        expanded={expanded}
      />

      {/* Logout */}
      <RailAction
        icon={LogOut}
        label="Sign out"
        onClick={logout}
        expanded={expanded}
        danger
      />
    </div>
  );
}
