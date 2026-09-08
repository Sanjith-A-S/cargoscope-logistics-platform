import React, { useState, useEffect, useContext, createContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardScreen from './pages/DashboardScreen';
import ShipmentScreen from './pages/ShipmentScreen';
import DataActivity from './pages/DataSources/DataActivity';
import CarrierPerformance from './pages/CarrierPerformance';
import SettingsScreen from './pages/SettingsScreen';
import AnomalyReview from './pages/AnomalyReview';
import LoginScreen from './pages/LoginScreen';
import UploadScreen from './pages/UploadScreen';
import NavRail from './components/NavRail';
import RiskQueueScreen from './features/risk_queue/RiskQueueScreen';
import { DatasetProvider } from './features/datasets/DatasetContext';
import AdminPortal from './features/admin/AdminPortal';

// ─── Auth Context ────────────────────────────────────────────────────────────
export const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

function AuthProvider({ children }) {
  // localStorage persists across page reloads (unlike sessionStorage which is tab-only)
  const [token, setToken] = useState(() => localStorage.getItem('auth_token'));

  const login = (newToken) => {
    localStorage.setItem('auth_token', newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Protected Route ─────────────────────────────────────────────────────────
function ProtectedRoute({ children }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

// ─── Admin Route — requires role:admin in JWT payload ─────────────────────────
function AdminRoute({ children }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  try {
    // Decode JWT payload without verifying signature (verification happens server-side)
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.role !== 'admin') return <Navigate to="/" replace />;
  } catch {
    return <Navigate to="/login" replace />;
  }
  return children;
}

// ─── Layout ───────────────────────────────────────────────────────────────────
const Layout = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

  return (
    <div className="layout-container">
      <NavRail theme={theme} onToggleTheme={toggleTheme} />
      <div className="content-wrapper">
        <main className="main-content">
          <div className="animate-fade-up">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginScreen />} />

          {/* Admin portal — completely separate from regular app, no NavRail */}
          <Route
            path="/admin/*"
            element={
              <AdminRoute>
                <AdminPortal />
              </AdminRoute>
            }
          />

          <Route
            path="/*"
            element={
              <ProtectedRoute>
                {/* DatasetProvider is inside ProtectedRoute so it only
                    fetches datasets when the user is authenticated */}
                <DatasetProvider>
                  <Layout>
                    <Routes>
                      {/* Risk Queue is the new home screen (spec §6) */}
                      <Route path="/"                 element={<RiskQueueScreen />} />
                      {/* Dashboard moved to /dashboard */}
                      <Route path="/dashboard"        element={<DashboardScreen />} />
                      <Route path="/shipments"        element={<ShipmentScreen />} />
                      <Route path="/carriers"         element={<CarrierPerformance />} />
                      <Route path="/anomalies"        element={<AnomalyReview />} />
                      <Route path="/sources/monitor"  element={<DataActivity />} />
                      {/* Upload — standalone top-level route, also reachable from Settings */}
                      <Route path="/upload"           element={<UploadScreen />} />
                      <Route path="/settings"         element={<SettingsScreen />} />
                    </Routes>
                  </Layout>
                </DatasetProvider>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
