# ValueMap site

Interactive companion to *Predicting Alignment Generalization with Value Representations*.
Vite + Svelte 5 + D3, deployed to GitHub Pages by `.github/workflows/deploy.yml` on push to `main`
(enable Pages → "GitHub Actions" in the repo settings).

## Layout

| path | what |
| --- | --- |
| `src/` | the app: `App.svelte`, `sections/S1–S4`, shared components in `lib/` (`meta.js` holds authors, links, BibTeX) |
| `public/data/` | exported JSON the site loads at runtime (committed; regenerate with the scripts below) |
| `public/assets/` | static assets (paper PDF) |
| `scripts/` | Python export pipeline reading `~/value-generalization` |
| `flame/` | prompt + extractor for pulling ConflictScope transcripts on flame |
| `raw/` | intermediate/untracked inputs (`flips_selected.json`, `transcripts/` from flame) |

## Develop

```bash
source ~/.nvm/nvm.sh && nvm use 22
npm install
npm run dev        # http://localhost:5173
npm run build      # -> dist/
```

## Regenerate data

Run with the value-generalization core env (`PY=~/value-generalization/.venvs/core/bin/python`):

```bash
cd scripts
$PY select_flips.py          # picks top-3 flip scenarios per cell -> raw/flips_selected.json, flame/flip_request.json
$PY export_data.py           # -> public/data/ (all sections); --only s1|s2|s3|s4
```

`export_data.py` asserts its numbers against the paper's own outputs: predictor ρ vs.
`notebooks/0917/7b-final/results.json`, ValueMap cluster sizes (70/55/52/89), and the coherence of
the 64 multi-value targets vs. `joined.csv`.

### Transcripts (Section 1 examples)

Fine-tuned model responses live on flame. Follow `flame/FLAME_PROMPT.md`, put the results at
`raw/transcripts/<arm>.jsonl.gz`, then rerun `$PY export_data.py --only s1`. Until then the
site shows real scenarios and judge scores with a "transcript pending" placeholder for the
DPO arms' base responses and all fine-tuned responses. SFT-arm base responses (urial0 base
evals) are already local.
