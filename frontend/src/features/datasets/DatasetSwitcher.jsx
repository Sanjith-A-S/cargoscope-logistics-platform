/**
 * features/datasets/DatasetSwitcher.jsx
 *
 * Dropdown shown in the NavRail header that lets users switch between
 * datasets without a page reload. Creates a new dataset inline.
 */
import React, { useState } from 'react';
import { useDataset } from './DatasetContext';
import { createDataset } from './api';

export default function DatasetSwitcher() {
  const { datasets, activeDataset, setActiveDataset, reload } = useDataset();
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [busy, setBusy] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setBusy(true);
    try {
      const ds = await createDataset(newName.trim());
      await reload();
      setActiveDataset(ds);
      setNewName('');
      setCreating(false);
    } catch {
      /* TODO: toast */
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="dataset-switcher">
      <div className="dataset-switcher__label">Dataset</div>
      <select
        className="dataset-switcher__select"
        value={activeDataset?.id ?? ''}
        onChange={e => {
          const found = datasets.find(d => d.id === parseInt(e.target.value));
          if (found) setActiveDataset(found);
        }}
      >
        {datasets.map(ds => (
          <option key={ds.id} value={ds.id}>
            {ds.name}
          </option>
        ))}
        {datasets.length === 0 && (
          <option disabled value="">
            No datasets yet
          </option>
        )}
      </select>

      {activeDataset && (
        <div className="dataset-switcher__meta">
          {activeDataset.source_row_count.toLocaleString()} rows
          {activeDataset.date_range_start && (
            <span>
              {' '}· {activeDataset.date_range_start.slice(0, 10)} → {activeDataset.date_range_end?.slice(0, 10)}
            </span>
          )}
        </div>
      )}

      {creating ? (
        <form className="dataset-switcher__create-form" onSubmit={handleCreate}>
          <input
            autoFocus
            className="dataset-switcher__input"
            placeholder="Dataset name…"
            value={newName}
            onChange={e => setNewName(e.target.value)}
          />
          <button type="submit" className="btn btn--xs btn--primary" disabled={busy}>
            {busy ? '…' : 'Create'}
          </button>
          <button type="button" className="btn btn--xs btn--ghost" onClick={() => setCreating(false)}>
            Cancel
          </button>
        </form>
      ) : (
        <button className="btn btn--xs btn--ghost dataset-switcher__new" onClick={() => setCreating(true)}>
          + New dataset
        </button>
      )}
    </div>
  );
}
