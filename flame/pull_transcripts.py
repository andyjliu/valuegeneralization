#!/usr/bin/env python3
"""Pull the ConflictScope transcripts the website needs out of full model_evals CSVs.

Stdlib only (no pandas needed). Usage:

    python3 pull_transcripts.py --request flip_request.json \
        --root /path/that/contains/data/gt [--root another/root ...] --out out/

For each arm in the request, it finds the run directory (by basename, e.g.
`const_v3_dpo_full49-0e440a7ad479`) under any --root, reads each requested CSV,
checks that each requested row's `likert` matches the expected value (proving
it is the same eval run the paper's matrices were built from), and writes
out/<arm>.jsonl.gz with one line per (file, scenario_id):

    {"file", "scenario_id", "likert", "choice", "conversation", "reasoning"}

plus out/report.json summarizing coverage and mismatches.
"""
import argparse
import csv
import gzip
import json
import os
import sys

csv.field_size_limit(sys.maxsize)


def find_run_dir(roots, run_basename):
    hits = []
    for root in roots:
        for dirpath, dirnames, _ in os.walk(root):
            if os.path.basename(dirpath) == run_basename and "model_evals" in dirnames:
                hits.append(os.path.join(dirpath, "model_evals"))
            # don't descend into huge irrelevant trees
            dirnames[:] = [d for d in dirnames if not d.startswith((".", "__"))
                           and d not in ("wandb", "checkpoints", "merged", "node_modules")]
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", default="flip_request.json")
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--evals-dir", action="append", default=[],
                    help="arm=path override, e.g. qwen_dpo=/x/y/model_evals")
    args = ap.parse_args()
    req = json.load(open(args.request))
    overrides = dict(s.split("=", 1) for s in args.evals_dir)
    os.makedirs(args.out, exist_ok=True)
    report = {}
    for arm, spec in req.items():
        run_base = os.path.basename(spec["run_dir"])
        if arm in overrides:
            cands = [overrides[arm]]
        else:
            cands = find_run_dir(args.root, run_base)
        rep = {"run_dir": run_base, "candidates": cands, "files": {}}
        report[arm] = rep
        if not cands:
            print(f"[{arm}] run dir {run_base} NOT FOUND under {args.root}")
            continue
        evals = cands[0]
        print(f"[{arm}] using {evals}")
        n_ok = n_bad = n_missing = n_empty = 0
        with gzip.open(os.path.join(args.out, f"{arm}.jsonl.gz"), "wt") as out:
            for fname, want in spec["files"].items():
                path = os.path.join(evals, fname)
                if not os.path.exists(path):
                    rep["files"][fname] = "missing file"
                    n_missing += len(want)
                    continue
                seen = set()
                with open(path, newline="") as f:
                    for row in csv.DictReader(f):
                        sid = row["scenario_id"]
                        if sid not in want or sid in seen:
                            continue
                        seen.add(sid)
                        try:
                            lik = float(row["likert"])
                        except ValueError:
                            lik = None
                        if lik is None or abs(lik - want[sid]) > 1e-6:
                            n_bad += 1
                        else:
                            n_ok += 1
                        if not (row.get("conversation") or "").strip():
                            n_empty += 1
                        out.write(json.dumps({
                            "file": fname, "scenario_id": sid, "likert": lik,
                            "choice": row.get("choice"),
                            "conversation": row.get("conversation"),
                            "reasoning": row.get("reasoning"),
                        }) + "\n")
                n_missing += len(set(want) - seen)
        rep.update(ok=n_ok, likert_mismatch=n_bad, missing_rows=n_missing,
                   empty_conversation=n_empty)
        print(f"[{arm}] ok={n_ok} likert_mismatch={n_bad} missing={n_missing} "
              f"empty_conversation={n_empty}")
    json.dump(report, open(os.path.join(args.out, "report.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
