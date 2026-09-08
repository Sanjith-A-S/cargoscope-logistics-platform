/**
 * features/datasets/DatasetContext.jsx
 *
 * Global dataset selection state. All analytics pages consume activeDataset.id.
 * On mount: fetches org's datasets; auto-selects the most-recently-updated one.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchDatasets } from './api';

const DatasetContext = createContext(null);

export function DatasetProvider({ children }) {
  const [datasets, setDatasets] = useState([]);
  const [activeDataset, setActiveDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const ds = await fetchDatasets();
      setDatasets(ds);
      // Auto-select latest unless user has already chosen one
      if (ds.length > 0) {
        setActiveDataset(prev =>
          prev ? (ds.find(d => d.id === prev.id) || ds[0]) : ds[0]
        );
      } else {
        setActiveDataset(null);
      }
    } catch (e) {
      setError('Could not load datasets.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return (
    <DatasetContext.Provider
      value={{ datasets, activeDataset, setActiveDataset, reload, loading, error }}
    >
      {children}
    </DatasetContext.Provider>
  );
}

export function useDataset() {
  const ctx = useContext(DatasetContext);
  if (!ctx) throw new Error('useDataset must be used inside <DatasetProvider>');
  return ctx;
}
