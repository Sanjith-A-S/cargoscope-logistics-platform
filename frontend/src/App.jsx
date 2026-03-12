import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, Package, Network, Settings, Compass, Search, Bell, Sun, Moon } from 'lucide-react';
import DashboardScreen from './pages/DashboardScreen';
import UploadScreen from './pages/UploadScreen';
import ShipmentScreen from './pages/ShipmentScreen';
import GraphScreen from './pages/GraphScreen';

const SidebarItem = ({ to, icon: Icon, label }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`sidebar-item ${isActive ? 'active' : ''}`}
    >
      <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
      <span>{label}</span>
    </Link>
  );
};

const Layout = ({ children }) => {
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="layout-container">
      {/* Sidebar */}
      <nav className="sidebar glass-panel">
        <div className="sidebar-header">
          <Compass size={28} color="var(--primary)" />
          <h2 style={{ fontSize: '20px', fontWeight: 700, letterSpacing: '-0.5px' }}>Trade Intel</h2>
        </div>
        <div className="sidebar-menu">
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8, paddingLeft: 16, letterSpacing: 1 }}>Analytics</div>
          <SidebarItem to="/" icon={LayoutDashboard} label="Dashboard" />
          <SidebarItem to="/shipments" icon={Package} label="Shipments Explorer" />
          <SidebarItem to="/graph" icon={Network} label="Knowledge Graph" />

          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: 20, marginBottom: 8, paddingLeft: 16, letterSpacing: 1 }}>Manage</div>
          <SidebarItem to="/upload" icon={UploadCloud} label="Upload Data" />
          <SidebarItem to="/settings" icon={Settings} label="Settings" />
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="content-wrapper">
        {/* Top Header */}
        <header className="top-header glass-header">
          <div className="header-search">
            <Search size={18} color="var(--text-muted)" />
            <input type="text" placeholder="Search shipments, origins..." />
          </div>
          <div className="header-actions">
            <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle Theme">
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button className="icon-btn" style={{ position: 'relative' }}>
              <Bell size={20} />
              <span style={{ position: 'absolute', top: 6, right: 8, width: 8, height: 8, background: 'var(--danger)', borderRadius: '50%' }}></span>
            </button>
            <div className="avatar">SA</div>
          </div>
        </header>

        {/* Page Content */}
        <main className="main-content">
          <div className="animate-slide-up">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardScreen />} />
          <Route path="/upload" element={<UploadScreen />} />
          <Route path="/shipments" element={<ShipmentScreen />} />
          <Route path="/graph" element={<GraphScreen />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
