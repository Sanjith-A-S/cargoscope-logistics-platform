/**
 * features/registry.js
 *
 * Feature flag registry. Each key maps to a boolean.
 * Components read from this file instead of checking env vars directly.
 * To add a feature: add one entry here + implement the component.
 * To remove: set to false (tree-shaking removes unused branches in production).
 */

const registry = {
  /** Multi-dataset selector in nav and upload flow */
  MULTI_DATASET: true,

  /** Live Risk Queue (Module 6) */
  RISK_QUEUE: true,

  /** OTIF metrics (Module 4) — shown in dashboard + carrier scorecard */
  OTIF: true,

  /** Weight-band breakdown in carrier scorecard (Module 8) */
  WEIGHT_BANDS: true,

  /** Lane summary table (Module 8) */
  LANE_SUMMARY: true,

  /** LLM narration — off by default; enabled when backend reports enabled=true */
  LLM_NARRATION: false,
};

export default registry;
