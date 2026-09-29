# Task: pull ConflictScope transcripts for the ValueMap website (run on flame)

You are running on the **flame** cluster. On the babel cluster we are building a website for the
paper *Predicting Alignment Generalization with Value Representations*. Its first figure shows, for
each cell (v1 trained, v2 evaluated) of the generalization matrices, a real ConflictScope scenario
where the model's behavior flipped after single-value training: **base model response → fine-tuned
response**, with judge scores.

The judge scores are already on babel, but the eval CSVs there have the `conversation` and `reasoning`
columns stripped (empty). The full CSVs should be on flame. Your job is to extract only the
~48k rows we need and package them for transfer.

## What you have

This directory (copied from babel `~/valuegeneralization/flame/`) contains:

- `flip_request.json` (~7 MB): for each of 4 arms, the eval run directory name and a map
  `{csv_filename: {scenario_id: expected_likert}}`.
- `pull_transcripts.py`: a stdlib-only extractor (Python 3.8+) that finds each run's
  `model_evals/` dir, reads the requested rows, **verifies the likert score matches**, and writes
  gzipped jsonl.

| arm | run dir basename | csv prefix | rows needed |
| --- | --- | --- | --- |
| olmo_dpo | `const_v3_dpo_full49_olmo3-2faecb31bb52` | `neutral_olmo-3_7b_*` (incl. `_base.csv`) | 11,351 |
| qwen_dpo | `const_v3_dpo_full49-0e440a7ad479` | `neutral_qwen3_8b_*` (incl. `_base.csv`) | 11,380 |
| olmo_sft | `const_v3_sft_full66_olmo3-1f6a32e2c24b` | `olmo-3_7b_base_*` (fine-tunes only) | 12,644 |
| qwen_sft | `const_v3_sft_full66-629ad9115f1c` | `qwen3_8b_base_*` (fine-tunes only) | 12,511 |

(SFT-arm base transcripts are already on babel. Don't look for them.)

## Steps

1. **Locate the eval outputs.** They are most likely in a value-generalization checkout's
   `data/gt/<run dir>/model_evals/` (e.g. `~/value-generalization`, or under `/project/flame/andyliu/`).
   Try, for example:
   `find ~ /project/flame/andyliu -maxdepth 6 -type d -name 'const_v3_*' 2>/dev/null`.
   The models themselves were at `/project/flame/andyliu/conflictscope-finetune/merged/`, so
   `conflictscope-finetune` is a good place to look if the valuegen layout isn't there.
   Each CSV has columns
   `scenario_id,value1,value2,user_model,assistant_model,judge_model,choice,likert,reasoning,conversation,generating_model`
   and 11,188 rows. Confirm the `conversation` column is non-empty before going further.
2. **Run the extractor**:
   ```bash
   python3 pull_transcripts.py --request flip_request.json \
       --root <dir containing the run dirs> [--root <another>] --out out/
   ```
   If a run dir has a different name or layout on flame, pass it explicitly:
   `--evals-dir qwen_dpo=/abs/path/to/model_evals` (repeatable).
3. **Check `out/report.json`.** For every arm we want `likert_mismatch == 0`,
   `missing_rows == 0`, and `empty_conversation == 0`. If there are small numbers of
   mismatches (<1%), that's acceptable; note them. If an arm has many mismatches, you probably found a
   different run (e.g. a re-eval); look for other candidates (`report.json` lists every candidate
   dir found) and re-run with `--evals-dir`. If the transcripts live somewhere else entirely (e.g.
   ConflictScope's raw jsonl output instead of these CSVs), adapt the script, keeping the same
   output schema and the likert check.
4. **Package**: `tar czf valuemap_transcripts.tgz out/` (expect roughly 50–150 MB).

## Where to put the result

Copy it back to babel and unpack it so the files land at:

```
babel:~/valuegeneralization/raw/transcripts/{olmo_dpo,olmo_sft,qwen_dpo,qwen_sft}.jsonl.gz
babel:~/valuegeneralization/raw/transcripts/report.json
```

For example, from flame:
`scp valuemap_transcripts.tgz babel:~/valuegeneralization/raw/` then on babel
`cd ~/valuegeneralization/raw && tar xzf valuemap_transcripts.tgz && mv out transcripts`.

Do **not** modify any eval files on flame. This task is read-only apart from `out/`.
When done, report the per-arm numbers from `report.json` and the paths you used.
