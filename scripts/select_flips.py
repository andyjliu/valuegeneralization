"""Pick per-cell flip examples from judge scores (no transcripts needed).

For arm a, trained value v1 and evaluated value v2, a scenario "flips" when the
v2-aligned score of the v1-finetune differs from the base model's by >= MIN_DELTA
in the direction of G(v1, v2). We keep the TOP_K largest flips per cell.

Writes
  raw/flips_selected.json   per-cell stats + chosen scenario ids and scores
  flame/flip_request.json   exactly which (csv, scenario_id) transcripts to pull on flame,
                            with the expected likert per row so flame can verify the match

With --arms a,b only those arms are selected: their entries are merged into the existing
raw/flips_selected.json and the request (written to --request) covers just those arms.
"""
import argparse
import json
from collections import defaultdict

import numpy as np
import pandas as pd

from common import ARMS, ARM_META, RAW, SITE, arm_rows, dump, frames, load_G

TOP_K = 3
MIN_DELTA = 0.5


def load_scores(path):
    d = pd.read_csv(path, usecols=["scenario_id", "value1", "value2", "likert"])
    d["likert"] = pd.to_numeric(d["likert"], errors="coerce")
    return d.set_index("scenario_id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", help="comma-separated subset of arms (default: all)")
    ap.add_argument("--request", default=str(SITE / "flame" / "flip_request.json"))
    args = ap.parse_args()
    arms = args.arms.split(",") if args.arms else ARMS
    assert set(arms) <= set(ARMS), arms
    _, all66 = frames()
    sel_path = RAW / "flips_selected.json"
    selected = json.load(open(sel_path)) if args.arms and sel_path.exists() else {}
    request = {}
    for arm in arms:
        meta = ARM_META[arm]
        evals = meta["run_dir"] / "model_evals"
        G = load_G(arm)
        base = load_scores(meta["base_csv"])
        base_local = meta["base_local"]
        # scenarios per evaluated value; aligned score = P(action for v2)
        by_v2 = {v: base.index[(base.value1 == v) | (base.value2 == v)] for v in all66}
        need = defaultdict(dict)
        arm_sel = {}
        for i, v1 in enumerate(arm_rows(arm)):
            fname = f"{meta['mtag']}_{v1}.csv"
            ft = load_scores(evals / fname).reindex(base.index)
            row = {}
            for j, v2 in enumerate(all66):
                ids = by_v2[v2]
                is_a = (base.loc[ids, "value1"] == v2).values
                lb, lf = base.loc[ids, "likert"].values, ft.loc[ids, "likert"].values
                sb = np.where(is_a, (1 - lb) / 2, (1 + lb) / 2)
                sf = np.where(is_a, (1 - lf) / 2, (1 + lf) / 2)
                ok = np.isfinite(sb) & np.isfinite(sf)
                delta = sf - sb
                g = float(G[i, j])
                sign = 1.0 if g >= 0 else -1.0
                toward = int(((delta >= MIN_DELTA) & ok).sum())
                away = int(((delta <= -MIN_DELTA) & ok).sum())
                cand = np.where(ok & (sign * delta >= MIN_DELTA))[0]
                cand = cand[np.lexsort((np.array(ids)[cand], -np.abs(delta[cand])))][:TOP_K]
                ex = []
                for k in cand:
                    sid = ids[k]
                    ex.append({"sid": sid, "base": round(float(sb[k]), 3),
                               "ft": round(float(sf[k]), 3)})
                    need[fname][sid] = float(lf[k])
                    if not base_local:
                        need[f"{meta['mtag']}_base.csv"][sid] = float(lb[k])
                row[v2] = {"g": round(g, 4), "n": int(ok.sum()), "toward": toward,
                           "away": away, "ex": ex}
            arm_sel[v1] = row
            print(f"{arm} {i + 1}/{len(arm_rows(arm))} {v1}", flush=True)
        selected[arm] = arm_sel
        request[arm] = {
            "run_dir": str(meta["run_dir"].relative_to(meta["run_dir"].parents[2])),
            "base_csv": str(meta["base_csv"]),
            "base_transcripts_local": base_local,
            "files": {f: dict(sorted(s.items())) for f, s in sorted(need.items())},
        }
        n_ids = sum(len(s) for s in need.values())
        print(f"== {arm}: {len(need)} csvs, {n_ids} (csv, scenario) transcripts requested")
    selected = {a: selected[a] for a in ARMS if a in selected}
    print("selected bytes", dump(selected, sel_path))
    with open(args.request, "w") as f:
        json.dump(request, f, indent=1)


if __name__ == "__main__":
    main()
