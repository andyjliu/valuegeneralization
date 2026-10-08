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

// model family x size x training method; the 7B arms keep their original ids
export const MODEL_LABEL = { olmo: 'Olmo-3', qwen: 'Qwen-3' };
// size buttons show the selected family's actual sizes
export const SIZE_LABEL = { olmo: { s: '7B', l: '32B' }, qwen: { s: '8B', l: '30B' } };
export const METHOD_LABEL = { dpo: 'DPO', sft: 'SFT' };
const MODEL_NAME = {
  olmo: { s: 'Olmo-3-7B', l: 'Olmo-3-32B' },
  qwen: { s: 'Qwen-3-8B', l: 'Qwen-3-30B-A3B' },
};
const SIZE_TAG = { olmo: { s: '', l: '32' }, qwen: { s: '', l: '30' } };
export const modelName = (model, size) => MODEL_NAME[model][size];
export const armId = (model, size, method) => `${model}${SIZE_TAG[model][size]}_${method}`;
export const ARMS = Object.keys(MODEL_LABEL).flatMap((model) =>
  ['s', 'l'].flatMap((size) =>
    Object.keys(METHOD_LABEL).map((method) => ({ id: armId(model, size, method), model, size, method }))));

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

// predictor identity colours (validated all-pairs on the light surface)
export const PRED_HEX = {
  persona: '#2a78d6',
  grad_proj: '#e34948',
  sentemb_behavior: '#1baf7a',
  weight_steer: '#eda100',
  sentence_emb: '#4a3aa7',
};
