#!/usr/bin/env python3
"""
gen_summary.py — Regenerate SUMMARY.md from benchmark CSV files.

Usage:
    python3 gen_summary.py [results_dir]
    python3 gen_summary.py ./results
"""

import csv
import os
import sys
from datetime import date

RESULTS_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results")
RESULTS_DIR = os.path.abspath(RESULTS_DIR)

# Model metadata: size on disk, parameter count, benchmark method, notes
MODELS = {
    "gpt-oss:20b":        {"size": "~11GB",  "params": "20B MoE",  "method": "flm bench",  "note": ""},
    "llama3.2:1b":        {"size": "~1.2GB", "params": "1B",       "method": "flm bench",  "note": ""},
    "llama3.2:3b":        {"size": "~2.7GB", "params": "3B",       "method": "flm bench",  "note": ""},
    "lfm2:1.2b":          {"size": "~0.9GB", "params": "1.2B",     "method": "flm bench",  "note": "Liquid AI"},
    "nanbeige4.1:3b":     {"size": "~2.9GB", "params": "3B",       "method": "flm bench",  "note": "3-iter estimate"},
    "qwen3:4b":           {"size": "~3.1GB", "params": "4B",       "method": "serve API",  "note": "slow prefill on NPU"},
    "qwen3:8b":           {"size": "~5.7GB", "params": "8B",       "method": "serve API",  "note": "1k context only"},
    "gemma3:4b":          {"size": "~4.6GB", "params": "4B",       "method": "serve API",  "note": "includes vision weights"},
    "llama3.1:8b":        {"size": "~5.5GB", "params": "8B",       "method": "serve API",  "note": ""},
    "deepseek-r1:8b":     {"size": "~5.5GB", "params": "8B",       "method": "serve API",  "note": "reasoning/R1 distill"},
    "phi4-mini-it:4b":    {"size": "~3.4GB", "params": "4B",       "method": "serve API",  "note": ""},
    "gemma4-it:e4b":      {"size": "~8.7GB", "params": "eff-4B",   "method": "serve API",  "note": "MoE + vision + audio"},
}

FILE_MAP = {
    model: f"bench_{model.replace(':', '_').replace('/', '_')}_20260528.csv"
    for model in MODELS
}

DISPLAY_ORDER = [
    "llama3.2:1b", "lfm2:1.2b", "llama3.2:3b", "nanbeige4.1:3b",
    "qwen3:4b", "phi4-mini-it:4b", "gemma3:4b",
    "qwen3:8b", "llama3.1:8b", "deepseek-r1:8b", "gemma4-it:e4b", "gpt-oss:20b",
]


def load_csv(path: str) -> dict:
    data = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            k = int(row["context_length_k"])
            data[k] = {
                "ttft":    float(row["ttft_avg_s"]),
                "prefill": float(row["prefill_avg_toks_per_s"]),
                "decode":  float(row["decoding_avg_toks_per_s"]),
            }
    return data


all_data: dict[str, dict] = {}
for model, fname in FILE_MAP.items():
    path = os.path.join(RESULTS_DIR, fname)
    if os.path.exists(path):
        all_data[model] = load_csv(path)

lines = []

lines += [
    "# FastFlowLM NPU Benchmark -- ASUS ROG Flow Z13",
    "",
    "**Hardware:** Ryzen AI Max+ 395 (Strix Halo) · XDNA2 NPU 50 TOPS · ~30GB available RAM",
    f"**Date:** {date.today().isoformat()}  **FLM:** NPU FW 1.1.2.65 / amdxdna 0.6",
    "**NPU power mode:** performance (default)",
    "",
    "## Benchmark Methods",
    "",
    "- **flm bench** (<=3B): built-in tool, 8 iterations x 6 context lengths (1k-32k tokens)",
    "- **serve API** (>=4B): custom script, 8 iterations x 5 context lengths (1k-16k);",
    "  32k context causes OOM at >=4B on this system's ~10GB NPU/shmem budget",
    "- All inference verified on `/dev/accel/accel0` (XDNA2 NPU) -- GPU held at 0% throughout",
    "",
    "---",
    "",
    "## Quick Comparison -- 1k Context (Typical Workload)",
    "",
    "| Model | Size | Params | TTFT (s) | Prefill (tok/s) | Decode (tok/s) | Notes |",
    "|---|---|---|---|---|---|---|",
]

for model in DISPLAY_ORDER:
    m = MODELS[model]
    d = all_data.get(model, {}).get(1, {})
    ttft    = f"{d['ttft']:.2f}"    if d else "N/A"
    prefill = f"{d['prefill']:.0f}" if d else "N/A"
    decode  = f"{d['decode']:.1f}"  if d else "N/A"
    lines.append(f"| {model} | {m['size']} | {m['params']} | {ttft} | {prefill} | {decode} | {m['note']} |")

lines += ["", "---", "", "## Full Results by Model", ""]

for model in DISPLAY_ORDER:
    m = MODELS[model]
    d = all_data.get(model, {})
    lines.append(f"### {model}  ({m['params']}, {m['size']})")
    method_line = f"Method: {m['method']}"
    if m["note"]:
        method_line += f"  |  {m['note']}"
    lines.append(method_line)
    lines += [
        "",
        "| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |",
        "|---|---|---|---|",
    ]
    for k in [1, 2, 4, 8, 16, 32]:
        if k in d:
            r = d[k]
            lines.append(f"| {k}k | {r['ttft']:.3f} | {r['prefill']:.1f} | {r['decode']:.1f} |")
        else:
            lines.append(f"| {k}k | -- | -- | -- |")
    lines.append("")

lines += [
    "---",
    "",
    "## Key Findings",
    "",
    "### 1. NPU Utilization Confirmed",
    "All models run exclusively on `/dev/accel/accel0` (XDNA2 NPU).",
    "The AMD Radeon GPU (`amdgpu`) held at **0%** throughout all inference.",
    "CPU usage during inference: ~0-18% (orchestration/host overhead only).",
    "",
    "### 2. Speed Champion: lfm2:1.2b (Liquid AI)",
    "**60.4 tok/s** decode at 1k context, maintaining **37.9 tok/s** at 32k.",
    "Best decode throughput and best decode/context-length retention of any model tested.",
    "Also the smallest model at ~0.9GB.",
    "",
    "### 3. Anomalous llama3.2:3b Behavior -- Decode Accelerates at Long Context",
    "Decode speed *increases* above 8k context: 19 tok/s at 8k rising to **37 tok/s at 16k**.",
    "FLM appears to switch to a more efficient NPU kernel tiling strategy at a context threshold.",
    "At 32k, the 3B model (33.4 tok/s) outperforms the 1B model (24.2 tok/s).",
    "",
    "### 4. Memory Constraint: ~10GB NPU/shmem Budget",
    "Available NPU shared memory: ~10GB for model weights + KV cache combined.",
    "- **<=3B models**: 32k context feasible (flm bench works fully)",
    "- **4B models**: 16k context max via serve mode; 32k OOMs",
    "- **8B models**: 16k viable for most; qwen3:8b crashed at 2k (architecture-dependent)",
    "Workaround: drop OS page cache (`echo 3 > /proc/sys/vm/drop_caches`) before each benchmark.",
    "",
    "### 5. Best 4B Model: phi4-mini-it:4b",
    "**19.7 tok/s** decode at 1k context -- highest of any 4B model tested.",
    "Strong prefill at 4k+ (~810 tok/s). Consistent across all context lengths.",
    "",
    "### 6. 8B Model Decode Floor: ~10-11 tok/s",
    "All three 8B models (llama3.1, deepseek-r1, qwen3) cluster at 10-11 tok/s at 1k,",
    "dropping to ~8.6 tok/s at 16k. llama3.1:8b and deepseek-r1:8b are essentially identical.",
    "",
    "### 7. qwen3:4b -- Anomalously Slow Prefill",
    "Prefill measured at **128 tok/s** vs 500-810 tok/s for other 4B models.",
    "Decode (23.9 tok/s) is in line with the family, suggesting the architecture is",
    "not well-matched to the XDNA2 prefill path. Needs re-verification.",
    "",
    "### 8. gpt-oss:20b -- MoE Efficiency Loss on XDNA2",
    "Despite 20B parameters, decode is only **19.2 tok/s** -- comparable to 4B models.",
    "Prefill at 1k (219 tok/s) is the lowest of any model. MoE routing overhead",
    "is not amortized efficiently on the XDNA2's fixed-function NPU columns.",
    "",
    "---",
    f"*Generated {date.today().isoformat()} · FastFlowLM NPU Benchmark Suite*",
]

out_path = os.path.join(RESULTS_DIR, "SUMMARY.md")
with open(out_path, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"Written: {out_path}")
