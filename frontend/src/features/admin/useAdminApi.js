/**
 * features/admin/useAdminApi.js
 *
 * Thin wrapper around apiService for admin endpoints.
 * All calls require a role:admin JWT — the backend enforces this with 403.
 */
import { useState, useCallback } from 'react';
import { apiService } from '../../services/apiService';

export function useAdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.adminGetUsers();
      setUsers(res.data.users || []);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  }, []);

  return { users, loading, error, refresh };
}

export function useAdminUserDatasets(userId) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.adminGetUserDatasets(userId);
      setDatasets(res.data.datasets || []);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load datasets.');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  return { datasets, loading, error, refresh };
}
