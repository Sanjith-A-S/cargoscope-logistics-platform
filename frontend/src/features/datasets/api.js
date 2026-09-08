/**
 * features/datasets/api.js — Dataset CRUD API calls.
 */
import api from '../../services/apiService';

export const fetchDatasets = () =>
  api.get('/datasets').then(r => r.data.datasets ?? []);

export const createDataset = (name) =>
  api.post('/datasets', { name }).then(r => r.data);
