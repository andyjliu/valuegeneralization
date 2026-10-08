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

`export_data.py` asserts its numbers against the paper's own outputs: predictor ρ and the
eight-setting aggregate vs. `notebooks/0924/rq1_eight_conditions/results.json` (which also
records the target and predictor files used for the ~32B arms), ValueMap cluster sizes (70/55/52/89), and the coherence of
the 64 multi-value targets vs. `joined.csv`.

### Transcripts (Section 1 examples)

Fine-tuned model responses live on flame. Follow `flame/FLAME_PROMPT.md`, put the results at
`raw/transcripts/<arm>.jsonl.gz`, then rerun `$PY export_data.py --only s1`. Until then the
site shows real scenarios and judge scores with a "transcript pending" placeholder. Only the
7B SFT arms' base responses (urial0 base evals) are local; every other base response and all
fine-tuned responses have to be pulled.

Arms (site id → eval run dir under `data/gt/`):

| arm | run dir | csv prefix |
| --- | --- | --- |
| `olmo_dpo` | `const_v3_dpo_full49_olmo3-2faecb31bb52` | `neutral_olmo-3_7b` |
| `olmo_sft` | `const_v3_sft_full66_olmo3-1f6a32e2c24b` | `olmo-3_7b_base` |
| `qwen_dpo` | `const_v3_dpo_full49-0e440a7ad479` | `neutral_qwen3_8b` |
| `qwen_sft` | `const_v3_sft_full66-629ad9115f1c` | `qwen3_8b_base` |
| `olmo32_dpo` | `const_v3_dpo_full49_olmo3_32b-66f7857035ca` | `neutral_olmo-3_32b` |
| `olmo32_sft` | `const_v3_sft_full66_olmo3_32b-7ec026a23d2a` | `olmo-3_32b_base` |
| `qwen30_dpo` | `const_v3_dpo_full49_qwen3_30b_a3b-54fbfe3f9393` | `neutral_qwen3_30b_a3b` |
| `qwen30_sft` | `const_v3_sft_full66_qwen3_30b_a3b-3baa45ab00cb` | `qwen3_30b_a3b_base` |

To add arms without redoing the others: `$PY select_flips.py --arms a,b --request ../flame/flip_request_32b.json`
(merges into `raw/flips_selected.json`, writes a request for just those arms).
