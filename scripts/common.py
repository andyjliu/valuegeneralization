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

ARMS = ["olmo_dpo", "olmo_sft", "qwen_dpo", "qwen_sft"]
ARM_META = {
    "olmo_dpo": dict(model="Olmo-3-7B", method="DPO", mtag="neutral_olmo-3_7b"),
    "olmo_sft": dict(model="Olmo-3-7B", method="SFT", mtag="olmo-3_7b_base"),
    "qwen_dpo": dict(model="Qwen-3-8B", method="DPO", mtag="neutral_qwen3_8b"),
    "qwen_sft": dict(model="Qwen-3-8B", method="SFT", mtag="qwen3_8b_base"),
}
for a in ARMS:
    stem = Path(MP.TARGETS[a])
    ARM_META[a]["run_dir"] = stem.parent.parent
    ARM_META[a]["stem"] = str(stem)
    # base-model eval the matrix was normalized against (see matrices/*_provenance.yaml).
    # SFT arms: urial0 base evals (full transcripts are local). DPO arms: neutral-SFT
    # base inside the run dir (transcripts stripped; pulled from flame).
    ARM_META[a]["base_csv"] = (
        ARM_META[a]["run_dir"] / "model_evals" / f"{ARM_META[a]['mtag']}_base.csv"
        if a.endswith("dpo") else
        VG / "data/gt/base_evals/conflictscope-93ad0f27231c" /
        ("Olmo-3-1025-7B_urial0_base.csv" if a.startswith("olmo") else "Qwen3-8B-Base_urial0_base.csv"))


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
    m, r, c = MP.load_ds_target(MP.TARGETS[arm])
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
