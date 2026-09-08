import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});

// ─── Request interceptor — attach JWT ─────────────────────────────────────────
api.interceptors.request.use((config) => {
    // localStorage persists across page reloads (fixes login persistence bug)
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ─── Response interceptor — handle 401 ───────────────────────────────────────
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;

export const apiService = {
    // ── Auth (new multi-tenant) ────────────────────────────────────────────────
    signup: async (email, password, orgName) => {
        return api.post('/auth/signup', { email, password, org_name: orgName });
    },

    login: async (email, password) => {
        return api.post('/auth/login', { email, password });
    },

    getMe: async () => {
        return api.get('/auth/me');
    },

    // ── Datasets ──────────────────────────────────────────────────────────────
    getDatasets: async () => {
        return api.get('/datasets');
    },

    createDataset: async (name) => {
        return api.post('/datasets', { name });
    },

    deleteDataset: async (datasetId) => {
        return api.delete(`/datasets/${datasetId}`);
    },

    // ── Upload ────────────────────────────────────────────────────────────────
    uploadDataset: async (file, datasetId = null) => {
        const formData = new FormData();
        formData.append('file', file);
        if (datasetId != null) {
            formData.append('dataset_id', datasetId);
        }
        return api.post('/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    // ── Analytics (all now accept optional datasetId) ─────────────────────────
    getDashboard: async (datasetId = null) => {
        const params = datasetId != null ? { dataset_id: datasetId } : {};
        return api.get('/analytics/dashboard', { params });
    },

    getShipments: async (page = 1, limit = 100, search = '', carrier = '', origin = '', status = '', sortBy = 'shipment_id', sortDesc = false, datasetId = null) => {
        const params = { page, limit, sort_by: sortBy, sort_desc: sortDesc };
        if (search)    params.search      = search;
        if (carrier)   params.carrier     = carrier;
        if (origin)    params.origin      = origin;
        if (status)    params.status      = status;
        if (datasetId) params.dataset_id  = datasetId;
        return api.get('/analytics/shipments', { params });
    },

    getCarrierRanking: async (datasetId = null) => {
        const params = datasetId != null ? { dataset_id: datasetId } : {};
        const response = await api.get('/analytics/carrier-ranking', { params });
        return response.data;
    },

    getCarrierRoutes: async (carrier, datasetId = null) => {
        const params = datasetId != null ? { dataset_id: datasetId } : {};
        const response = await api.get(`/analytics/carrier/${encodeURIComponent(carrier)}/routes`, { params });
        return response.data;
    },

    // ── OTIF (Module 4) ───────────────────────────────────────────────────────
    getOTIF: async (datasetId) => {
        return api.get('/analytics/otif', { params: { dataset_id: datasetId } });
    },

    // ── Risk Queue (Module 6) ─────────────────────────────────────────────────
    getRiskQueue: async (datasetId) => {
        return api.get('/risk-queue', { params: { dataset_id: datasetId } });
    },

    // ── Cost Intelligence v2 (Module 8) ───────────────────────────────────────
    getLanes: async (datasetId) => {
        return api.get('/analytics/lanes', { params: { dataset_id: datasetId } });
    },

    getAnomaliesV2: async (datasetId) => {
        return api.get('/analytics/anomalies-v2', { params: { dataset_id: datasetId } });
    },

    // ── Insights (legacy, kept for backward compat) ───────────────────────────
    getInsights: async (datasetId = null) => {
        const params = datasetId != null ? { dataset_id: datasetId } : {};
        return api.get('/insights/', { params });
    },

    predictDelay: async (payload) => {
        return api.post('/insights/predict', payload);
    },

    getAnomalies: async (datasetId = null) => {
        const params = datasetId != null ? { dataset_id: datasetId } : {};
        return api.get('/insights/anomalies', { params });
    },

    updateAnomalyStatus: async (shipmentId, status, notes = '') => {
        return api.patch(`/insights/anomalies/${encodeURIComponent(shipmentId)}`, { status, notes });
    },

    // ── Pipeline logs ─────────────────────────────────────────────────────────
    getPipelineLogs: async (limit = 50) => {
        const response = await api.get(`/logs?limit=${limit}`);
        return response.data;
    },

    // ── Narration (Module 9 — stub) ───────────────────────────────────────────
    getNarrationStatus: async () => {
        return api.get('/narration/status');
    },

    summarize: async (payload, contextType) => {
        return api.post('/narration/summarize', { payload, context_type: contextType });
    },

    // ── Admin (Module 11) — require role:admin JWT ────────────────────────────
    adminGetUsers: async () => {
        return api.get('/admin/users');
    },

    adminDeleteUser: async (userId) => {
        return api.delete(`/admin/users/${userId}`);
    },

    adminGetUserDatasets: async (userId) => {
        return api.get(`/admin/users/${userId}/datasets`);
    },

    adminDeleteDataset: async (datasetId) => {
        return api.delete(`/admin/datasets/${datasetId}`);
    },
};
