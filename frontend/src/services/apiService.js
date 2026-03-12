import axios from 'axios';

// Default FastAPI backend port
const API_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const apiService = {
    uploadDataset: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        return api.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    getDashboard: async () => {
        return api.get('/analytics/dashboard');
    },

    getShipments: async (skip = 0, limit = 100) => {
        return api.get(`/analytics/shipments?skip=${skip}&limit=${limit}`);
    },

    getInsights: async () => {
        return api.get('/insights/');
    }
};
