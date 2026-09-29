"""Export everything the site needs into public/data/.

    ~/value-generalization/.venvs/core/bin/python scripts/export_data.py [--only s1,s2,s3,s4]

Sections
  s1  values.json, g_<arm>.json, flips/<arm>/<row>.json     (needs raw/flips_selected.json)
  s2  leaderboard.json, predictors_<arm>.json
  s3  taxonomy.json
  s4  multivalue.json

Transcripts for flip examples are read from raw/transcripts/<arm>.jsonl.gz (pulled from
flame, see flame/FLAME_PROMPT.md) and, for the SFT arms' base model, from the local
urial0 base evals. Missing transcripts are replaced by clearly-flagged placeholders.
"""
import argparse
import csv
import gzip
import json
import re
import sys
import zlib
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from common import ARMS, ARM_META, MP, OUT, RAW, VG, arm_rows, constitution, dump, frames, load_G

csv.field_size_limit(sys.maxsize)

PRED_ORDER = ["persona", "grad_proj", "sentemb_behavior", "weight_steer", "sentence_emb"]
PRED_LABEL = {"sentence_emb": "Description-Embd", "sentemb_behavior": "Behavior-Embd",
              "persona": "Persona", "grad_proj": "Gradient", "weight_steer": "Weight"}
FIGS = VG / "notebooks/0924/iclr-figs-clean"
TURN_CHARS = 700        # per conversation turn shown on the site
PROMPT_CHARS = 1400     # scenario prompt
JUDGE_CHARS = 350       # judge reasoning for the fine-tuned response
MAX_TURNS = 3           # turns after the opening user message
MAX_EX = 3              # flip examples per cell


def pretty(slug):
    s = slug.replace("_", " ")
    return s[:1].upper() + s[1:]


def clip(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


# ─────────────────────────────── Section 1 ────────────────────────────────
def export_values():
    rows49, all66 = frames()
    desc = constitution()
    vals = [{"id": v, "name": pretty(v), "desc": desc[v], "trained": v in set(rows49)}
            for v in all66]
    print("values.json", dump(vals, OUT / "values.json"))
    return {v: i for i, v in enumerate(all66)}


def split_turns(conv):
    """'USER: ...\\n\\nASSISTANT: ...' -> [{'r': 'user'|'assistant', 't': str}]"""
    parts = re.split(r"(?:^|\n)(USER|ASSISTANT):\s?", conv or "")
    turns = []
    for role, text in zip(parts[1::2], parts[2::2]):
        turns.append({"r": role.lower(), "t": text.strip()})
    return turns


def response_turns(conv):
    """Everything after the opening user message, clipped for the site."""
    turns = split_turns(conv)
    if turns and turns[0]["r"] == "user":
        turns = turns[1:]
    return [{"r": t["r"], "t": clip(t["t"], TURN_CHARS)} for t in turns[:MAX_TURNS]]


def load_transcripts(arm):
    """{(csv filename, scenario_id): (conversation, reasoning)}"""
    tx = {}
    p = RAW / "transcripts" / f"{arm}.jsonl.gz"
    if p.exists():
        with gzip.open(p, "rt") as f:
            for line in f:
                r = json.loads(line)
                if (r.get("conversation") or "").strip():
                    tx[(r["file"], r["scenario_id"])] = (r["conversation"], r.get("reasoning"))
    base_csv = ARM_META[arm]["base_csv"]
    if base_csv.parent.name == "conflictscope-93ad0f27231c":   # local, full transcripts
        with open(base_csv, newline="") as f:
            for r in csv.DictReader(f):
                tx[("__base__", r["scenario_id"])] = (r["conversation"], r["reasoning"])
    return tx


N_BUCKETS = 64


def bucket(sid):
    return zlib.crc32(sid.encode()) % N_BUCKETS


def export_s1():
    """g_<arm>.json (matrix + flip counts), flips/<arm>/<row>.json (fine-tuned responses per
    cell) and scen/<bucket>.json (scenario text + each arm's base response, deduplicated)."""
    vidx = export_values()
    _, all66 = frames()
    sel = json.load(open(RAW / "flips_selected.json"))
    scen = pd.read_csv(VG / "data/scenarios/const_v3_cs/Qwen3.6-27B.csv",
                       usecols=["scenario_id", "action1", "action2", "value1", "value2"]
                       ).set_index("scenario_id")
    prompts = json.load(open(VG / "data/scenarios/const_v3_cs/cache.json"))
    store = {}
    for arm in ARMS:
        meta = ARM_META[arm]
        rows = arm_rows(arm)
        G = load_G(arm)
        cells = [sel[arm][v1][v2] for v1 in rows for v2 in all66]
        dump({"arm": arm, "model": meta["model"], "method": meta["method"],
              "rows": [vidx[v] for v in rows], "cols": [vidx[v] for v in all66],
              "g": [int(round(x * 1000)) for x in G.ravel()],
              "n": [c["n"] for c in cells], "toward": [c["toward"] for c in cells],
              "away": [c["away"] for c in cells]}, OUT / f"g_{arm}.json")
        tx = load_transcripts(arm)
        base_file = f"{meta['mtag']}_base.csv" if arm.endswith("dpo") else "__base__"
        n_real = n_mock = total = 0
        for i, v1 in enumerate(rows):
            ft_file = f"{meta['mtag']}_{v1}.csv"
            out_cells = []
            for v2 in all66:
                exs = []
                for e in sel[arm][v1][v2]["ex"][:MAX_EX]:
                    sid = e["sid"]
                    b, f = tx.get((base_file, sid)), tx.get((ft_file, sid))
                    mock = b is None or f is None
                    n_mock += mock
                    n_real += not mock
                    exs.append({"s": sid, "k": bucket(sid), "b": e["base"], "f": e["ft"],
                                "mock": mock, "ft": response_turns(f[0]) if f else [],
                                "fj": clip(f[1], JUDGE_CHARS) if f and isinstance(f[1], str) else None})
                    if sid not in store:
                        s = scen.loc[sid]
                        store[sid] = {"p": clip(prompts[sid], PROMPT_CHARS),
                                      "a1": s["action1"], "a2": s["action2"],
                                      "v1": vidx[s["value1"]], "v2": vidx[s["value2"]], "base": {}}
                    if arm not in store[sid]["base"]:
                        store[sid]["base"][arm] = response_turns(b[0]) if b else []
                out_cells.append(exs)
            total += dump({"v1": vidx[v1], "cells": out_cells}, OUT / "flips" / arm / f"{i}.json")
        print(f"{arm}: flips {total / 1e6:.1f} MB, real={n_real} placeholder={n_mock}")
    by_bucket = {}
    for sid, rec in store.items():
        by_bucket.setdefault(bucket(sid), {})[sid] = rec
    total = sum(dump(v, OUT / "scen" / f"{k}.json") for k, v in by_bucket.items())
    print(f"scen: {len(store)} scenarios, {total / 1e6:.1f} MB in {len(by_bucket)} buckets")


# ─────────────────────────────── Section 2 ────────────────────────────────
def pct_rank(x):
    return (rankdata(x) - 1) / (len(x) - 1) * 100


def export_s2():
    from valuegen.analysis import correlate as C
    rows49, all66 = frames()
    vidx = {v: i for i, v in enumerate(all66)}
    off = C.offdiag_mask(rows49, all66)
    res = json.load(open(VG / "notebooks/0917/7b-final/results.json"))
    board = {"preds": [{"id": p, "label": PRED_LABEL[p]} for p in PRED_ORDER],
             "arms": [], "rho": {}, "ci": {}, "ceiling": {},
             "aggregate": {p: res["fig2_aggregate"][p] for p in PRED_ORDER}}
    rng = np.random.default_rng(0)
    boot_idx = [rng.integers(0, len(rows49), len(rows49)) for _ in range(1000)]
    for arm in ARMS:
        m, r, c = MP.load_ds_target(MP.TARGETS[arm])
        T = C.reindex(m, r, c, rows49, all66)
        ok = off & np.isfinite(T)
        gp = np.full(T.shape, np.nan)
        gp[ok] = pct_rank(T[ok])
        out = {"arm": arm, "rows": [vidx[v] for v in rows49], "cols": [vidx[v] for v in all66],
               "gpct": [None if np.isnan(x) else int(round(x)) for x in gp.ravel()],
               "preds": {}}
        board["arms"].append({"id": arm, **{k: ARM_META[arm][k] for k in ("model", "method")}})
        board["ceiling"][arm] = float(MP.symmetric_ceiling(T, rows49, all66))
        board["rho"][arm], board["ci"][arm] = {}, {}
        for p in PRED_ORDER:
            pm, pr, pc = MP.load_pred(MP.pred_path(p, arm))
            P = C.reindex(pm, pr, pc, rows49, all66)
            rho = float(MP.offdiag_rho(T, P, rows49, all66))
            want = res["fig2_predictor_rho"][p][arm]
            assert abs(rho - want) < 1e-6, (arm, p, rho, want)
            boots = [MP._rho_on_rows(T, P, off, idx) for idx in boot_idx]
            board["rho"][arm][p] = rho
            board["ci"][arm][p] = [float(np.nanpercentile(boots, 2.5)),
                                   float(np.nanpercentile(boots, 97.5))]
            okp = ok & np.isfinite(P)
            pp = np.full(T.shape, np.nan)
            pp[okp] = pct_rank(P[okp])
            resid = np.abs(pp - gp)
            out["preds"][p] = {
                "cos": [None if not np.isfinite(x) else round(float(x), 3) for x in P.ravel()],
                "pct": [None if np.isnan(x) else int(round(x)) for x in pp.ravel()],
                "resid": [None if np.isnan(x) else int(round(x)) for x in resid.ravel()],
            }
        print(f"predictors_{arm}.json", dump(out, OUT / f"predictors_{arm}.json"))
    print("leaderboard.json", dump(board, OUT / "leaderboard.json"))


# ─────────────────────────────── Section 3 ────────────────────────────────
CLUSTER_NAME = {"personal_growth": "Attunement", "structured_and_methodical_reasoning": "Rigor",
                "professional_ethics_and_integrity": "Integrity", "risk_management": "Stewardship"}
CLUSTER_ORDER = ["Attunement", "Rigor", "Integrity", "Stewardship"]
CLUSTER_DESC = {
    "Attunement": "Supporting healthy interpersonal relationships and emotional growth in users.",
    "Rigor": "Supporting rigorous reasoning, objectivity, and excellence in task execution.",
    "Integrity": "Supporting professional norms and codes of conduct, and being intellectually "
                 "honest and truth-seeking.",
    "Stewardship": "Supporting the long-term welfare of society and the full consideration of "
                   "third parties.",
}
# the exemplar labels drawn on the paper's Fig. 4
FIG4_LABELS = ["diplomatic_communication", "compassionate_care_and_support",
               "communicative_clarity_and_precision", "analytical_rigor_and_precision",
               "consumer_and_client_protection", "privacy_and_confidentiality",
               "preventative_wellness_approaches", "strategic_foresight"]


def export_s3():
    base = FIGS / "rq3_functional_taxonomy/inputs"
    sim = np.load(base / "persona_L32_olmo3_32b.npy")
    values = json.load(open(base / "persona_L32_olmo3_32b_values.json"))
    coords = np.load(FIGS / "appI_taxonomy_comparison/inputs/mds_nonmetric_olmo3_32b.npy")
    assert json.load(open(FIGS / "appI_taxonomy_comparison/inputs/persona_values_olmo3_32b.json")) == values
    cl = pd.read_csv(base / "clusters_k4_olmo3_32b.csv").set_index("value")
    medoids = cl[cl.is_medoid.astype(bool)]
    cid_name = {int(r.cluster): CLUSTER_NAME[v] for v, r in medoids.iterrows()}
    desc = json.load(open(VG / "value_sets/vitw_l1_266.json"))
    missing = [v for v in FIG4_LABELS if v not in values]
    assert not missing, missing
    pts = []
    for i, v in enumerate(values):
        s = sim[i].copy()
        s[i] = -np.inf
        nn = np.argsort(-s)[:3]
        pts.append({"id": v, "name": pretty(v), "desc": desc.get(v, ""),
                    "c": CLUSTER_ORDER.index(cid_name[int(cl.loc[v, "cluster"])]),
                    "x": round(float(coords[i, 0]), 4), "y": round(float(coords[i, 1]), 4),
                    "nn": [[int(j), round(float(sim[i, j]), 3)] for j in nn],
                    "medoid": bool(cl.loc[v, "is_medoid"]), "label": v in FIG4_LABELS})
    sizes = [sum(p["c"] == k for p in pts) for k in range(4)]
    assert sizes == [70, 55, 52, 89], sizes
    out = {"clusters": [{"name": n, "desc": CLUSTER_DESC[n], "n": sizes[k]}
                        for k, n in enumerate(CLUSTER_ORDER)], "points": pts}
    print("taxonomy.json", dump(out, OUT / "taxonomy.json"))


# ─────────────────────────────── Section 4 ────────────────────────────────
def cos_matrix(npz, order):
    z = np.load(npz)
    X = np.stack([z[v] for v in order]).astype(np.float64)
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    return X @ X.T


def export_s4(n_samples=20000, kmax=15):
    _, all66 = frames()
    vidx = {v: i for i, v in enumerate(all66)}
    ex = VG / "data/exports/rq3_embeddings"
    mats = {"persona": cos_matrix(ex / "persona_qwen3_8b_neutral_sft_response_avg_L18.npz", all66),
            "description": cos_matrix(ex / "sentence_emb_mpnet.npz", all66)}
    rng = np.random.default_rng(0)
    iu = {k: np.triu_indices(k, 1) for k in range(2, kmax + 1)}
    quant = {e: {} for e in mats}
    for k in range(2, kmax + 1):
        sets = np.stack([rng.choice(66, k, replace=False) for _ in range(n_samples)])
        for e, M in mats.items():
            sub = M[sets[:, :, None], sets[:, None, :]]
            coh = sub[:, iu[k][0], iu[k][1]].mean(axis=1)
            quant[e][k] = [round(float(q), 4) for q in np.quantile(coh, np.linspace(0, 1, 101))]
    # the 64 trained 6-value targets (paper §5)
    cells = pd.read_csv(VG / "notebooks/0924/multivalue_synergy/data/ew64/ew64_cells.csv")
    joined = pd.read_csv(FIGS / "rq2_persona_similarity_predicts_robustness/inputs/joined.csv")
    joined = joined.set_index("arm_id")
    presets = []
    for arm_id, g in cells.groupby("arm_id", sort=True):
        ids = [vidx[v] for v in g.value]
        coh = float(np.mean([mats["persona"][a, b] for a, b in combinations(ids, 2)]))
        want = float(joined.loc[arm_id, "persona.tightness"])
        assert abs(coh - want) < 1e-4, (arm_id, coh, want)
        presets.append({"id": arm_id, "values": ids, "coh": round(coh, 4),
                        "robust": round(float(joined.loc[arm_id, "prefill.retention_norm.estimate"]), 4)})
    out = {"cos": {e: [[round(float(x), 4) for x in row] for row in M] for e, M in mats.items()},
           "quantiles": quant, "kmax": kmax, "n_samples": n_samples, "presets": presets}
    print("multivalue.json", dump(out, OUT / "multivalue.json"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="s1,s2,s3,s4")
    only = set(ap.parse_args().only.split(","))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in [("s1", export_s1), ("s2", export_s2), ("s3", export_s3), ("s4", export_s4)]:
        if name in only:
            fn()
