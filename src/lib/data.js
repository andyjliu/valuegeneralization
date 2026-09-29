// Cached JSON loaders for public/data (resolved relative to the page, so the
// site works under any GitHub Pages path).
const cache = new Map();

export function load(path) {
  if (!cache.has(path)) {
    const p = fetch(`./data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`${path}: ${r.status}`);
      return r.json();
    });
    p.catch(() => cache.delete(path));
    cache.set(path, p);
  }
  return cache.get(path);
}

export const ARMS = [
  { id: 'olmo_dpo', model: 'olmo', method: 'dpo' },
  { id: 'olmo_sft', model: 'olmo', method: 'sft' },
  { id: 'qwen_dpo', model: 'qwen', method: 'dpo' },
  { id: 'qwen_sft', model: 'qwen', method: 'sft' },
];
export const MODEL_LABEL = { olmo: 'Olmo-3-7B', qwen: 'Qwen-3-8B' };
export const METHOD_LABEL = { dpo: 'DPO', sft: 'SFT' };
export const armId = (model, method) => `${model}_${method}`;

export const CLUSTER_VARS = ['--c-attunement', '--c-rigor', '--c-integrity', '--c-stewardship'];
// same hue per cluster as the paper's Fig. 4: Attunement, Rigor, Integrity, Stewardship
export const CLUSTER_HEX = ['#2a78d6', '#eb6834', '#1baf7a', '#4a3aa7'];

export function fmtPct(x) {
  return `${Math.round(Math.abs(x) * 100)}%`;
}

// diverging scale for G in [-1, 1]
import { interpolateLab } from 'd3-interpolate';
const NEG = '#1c5cab', MID = '#f0efec', POS = '#b8312f';
const iNeg = interpolateLab(MID, NEG), iPos = interpolateLab(MID, POS);
export function divColor(g) {
  if (g == null || Number.isNaN(g)) return '#ffffff';
  const t = Math.min(1, Math.abs(g) / 0.8); // saturate at |G| = 0.8
  return g >= 0 ? iPos(t) : iNeg(t);
}
export const DIV_STOPS = { NEG, MID, POS };
