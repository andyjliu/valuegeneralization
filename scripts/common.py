"""Shared paths + loaders for the site export scripts.

Run with the value-generalization core env:
    ~/value-generalization/.venvs/core/bin/python scripts/<script>.py
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np

VG = Path(os.environ.get("VG_ROOT", Path.home() / "value-generalization"))
SITE = Path(__file__).resolve().parent.parent
RAW = SITE / "raw"
OUT = SITE / "public" / "data"

sys.path.insert(0, str(VG / "src"))

# The paper's own figure code is the source of truth for targets + predictor paths.
_spec = importlib.util.spec_from_file_location(
    "make_plots", VG / "notebooks/0917/7b-final/make_plots.py")
MP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MP)

# Canonical eight-condition scoring (7B + ~32B arms): per-arm rho, the aggregate, and the
# exact target / predictor files each number was computed from.
RES8 = json.load(open(VG / "notebooks/0924/rq1_eight_conditions/results.json"))

ARMS = ["olmo_dpo", "olmo_sft", "qwen_dpo", "qwen_sft",
        "olmo32_dpo", "olmo32_sft", "qwen30_dpo", "qwen30_sft"]
# size: "s" (~7B) or "l" (~32B); key8: this arm's id in RES8
ARM_META = {
    "olmo_dpo": dict(model="Olmo-3-7B", method="DPO", size="s", mtag="neutral_olmo-3_7b", key8="olmo_dpo_7b"),
    "olmo_sft": dict(model="Olmo-3-7B", method="SFT", size="s", mtag="olmo-3_7b_base", key8="olmo_sft_7b"),
    "qwen_dpo": dict(model="Qwen-3-8B", method="DPO", size="s", mtag="neutral_qwen3_8b", key8="qwen_dpo_7b"),
    "qwen_sft": dict(model="Qwen-3-8B", method="SFT", size="s", mtag="qwen3_8b_base", key8="qwen_sft_7b"),
    "olmo32_dpo": dict(model="Olmo-3-32B", method="DPO", size="l", mtag="neutral_olmo-3_32b", key8="olmo_dpo_30b"),
    "olmo32_sft": dict(model="Olmo-3-32B", method="SFT", size="l", mtag="olmo-3_32b_base", key8="olmo_sft_30b"),
    "qwen30_dpo": dict(model="Qwen-3-30B-A3B", method="DPO", size="l", mtag="neutral_qwen3_30b_a3b", key8="qwen_dpo_30b"),
    "qwen30_sft": dict(model="Qwen-3-30B-A3B", method="SFT", size="l", mtag="qwen3_30b_a3b_base", key8="qwen_sft_30b"),
}
# the only base evals whose full transcripts are on this machine (7B urial0 bases)
LOCAL_BASE_DIR = "conflictscope-93ad0f27231c"
# 7B targets come from the paper's figure code; the ~32B ones from RES8's recorded sources
TARGETS = {a: MP.TARGETS[a] if a in MP.TARGETS else RES8["sources"][ARM_META[a]["key8"]]["target"]
           for a in ARMS}
for a in ARMS:
    stem = Path(TARGETS[a])
    ARM_META[a]["run_dir"] = stem.parent.parent
    ARM_META[a]["stem"] = str(stem)
    # base-model eval the matrix was normalized against (see matrices/*_provenance.yaml).
    # 7B SFT arms: urial0 base evals (full transcripts are local). All other arms: the
    # base eval inside the run dir (transcripts stripped; pulled from the training cluster).
    ARM_META[a]["base_csv"] = (
        VG / "data/gt/base_evals" / LOCAL_BASE_DIR /
        ("Olmo-3-1025-7B_urial0_base.csv" if a.startswith("olmo") else "Qwen3-8B-Base_urial0_base.csv")
        if a in ("olmo_sft", "qwen_sft") else
        ARM_META[a]["run_dir"] / "model_evals" / f"{ARM_META[a]['mtag']}_base.csv")
    ARM_META[a]["base_local"] = ARM_META[a]["base_csv"].parent.name == LOCAL_BASE_DIR


def pred_path(pred, arm):
    """Base-matched predictor grid for (predictor, arm)."""
    if arm in MP.TARGETS:
        return MP.pred_path(pred, arm)
    return RES8["sources"][ARM_META[arm]["key8"]]["predictors"][pred]


def frames():
    """(rows49, all66): the paper's canonical row/col order (make_heatmaps.py)."""
    _, rows49, cols66 = MP.load_ds_target(MP.TARGETS["qwen_dpo"])
    all66 = list(rows49) + [c for c in cols66 if c not in set(rows49)]
    return list(rows49), all66


def arm_rows(arm):
    rows49, all66 = frames()
    return rows49 if arm.endswith("dpo") else all66


def load_G(arm):
    """ds-metric G reindexed onto (arm_rows, all66)."""
    from valuegen.analysis import correlate as C
    m, r, c = MP.load_ds_target(TARGETS[arm])
    _, all66 = frames()
    return C.reindex(m, r, c, arm_rows(arm), all66)


def constitution():
    return json.load(open(VG / "value_sets/constitution_tenets_v3.json"))


def dump(obj, path, **kw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, separators=(",", ":"), **kw)
    return path.stat().st_size
