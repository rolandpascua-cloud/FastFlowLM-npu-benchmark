#!/usr/bin/env python3
"""
bench_serve.py — FastFlowLM serve-based benchmark for 4B+ models.

Uses the FLM OpenAI-compatible API to benchmark models that exceed
the flm bench memory budget at 32k context. Runs 8 iterations at
1k, 2k, 4k, 8k, and 16k token contexts.

Usage:
    python3 bench_serve.py <model_tag>
    python3 bench_serve.py gemma3:4b
"""

import csv
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from subprocess import Popen, DEVNULL

MODEL = sys.argv[1] if len(sys.argv) > 1 else (print("Usage: bench_serve.py <model>") or sys.exit(1))
CTX_LENGTHS = [1, 2, 4, 8, 16]   # in thousands of tokens
ITERATIONS  = 8
PORT        = 8765
RESULTS_DIR = os.path.expanduser("~/fastflowlm-npu-benchmark/results")

FILLER = (
    "The quick brown fox jumps over the lazy dog. " * 500
    + "In a distant future humanity had spread across the stars. " * 500
)


def make_prompt(target_tokens: int) -> str:
    chars = target_tokens * 4 - 200  # ~4 chars/token, leave headroom for response
    return FILLER[:chars] + " Summarize the above in one sentence."


def start_server(ctx_limit: int) -> Popen:
    proc = Popen(
        ["flm", "serve", MODEL, "--port", str(PORT), "--ctx-len", str(ctx_limit)],
        stdout=DEVNULL,
        stderr=DEVNULL,
    )
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/v1/models", timeout=2)
            return proc
        except Exception:
            time.sleep(2)
    proc.terminate()
    raise RuntimeError("Server did not start within 60 seconds")


def query(prompt: str) -> dict:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50,
    }).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


os.makedirs(RESULTS_DIR, exist_ok=True)
print(f"Starting flm serve for {MODEL}...")
ctx_limit = max(CTX_LENGTHS) * 1024 + 512
server = start_server(ctx_limit)
print(f"Server ready (PID {server.pid})")

results: dict[int, dict] = {}
try:
    for ctx_k in CTX_LENGTHS:
        prompt = make_prompt(ctx_k * 1024)
        ttfts, prefills, decodes = [], [], []
        print(f"\n--- {ctx_k}k context ---")
        for i in range(ITERATIONS):
            try:
                resp = query(prompt)
                u = resp["usage"]
                ttft    = u.get("prefill_duration_ttft", 0)
                prefill = u.get("prefill_speed_tps", 0)
                decode  = u.get("decoding_speed_tps", 0)
                ttfts.append(ttft)
                prefills.append(prefill)
                decodes.append(decode)
                print(f"  iter {i+1}: TTFT={ttft:.3f}s  prefill={prefill:.1f}  decode={decode:.1f}")
            except Exception as e:
                print(f"  iter {i+1} FAILED: {e}")
        if ttfts:
            results[ctx_k] = {
                "ttft_avg":    statistics.mean(ttfts),
                "ttft_std":    statistics.stdev(ttfts) if len(ttfts) > 1 else 0,
                "ttft_min":    min(ttfts),
                "ttft_max":    max(ttfts),
                "prefill_avg": statistics.mean(prefills),
                "prefill_std": statistics.stdev(prefills) if len(prefills) > 1 else 0,
                "prefill_min": min(prefills),
                "prefill_max": max(prefills),
                "decode_avg":  statistics.mean(decodes),
                "decode_std":  statistics.stdev(decodes) if len(decodes) > 1 else 0,
                "decode_min":  min(decodes),
                "decode_max":  max(decodes),
            }
finally:
    server.terminate()
    server.wait()

print(f"\n{'=== Benchmark Results (via API) ===':}")
print(f"\n{'Context':>14} | {'TTFT (s)':>21} | {'Prefill (tok/s)':>25} | {'Decode (tok/s)':>24}")
print("-" * 92)
for k, v in sorted(results.items()):
    print(
        f" {str(k) + 'k':>14} | {v['ttft_avg']:>8.3f} ± {v['ttft_std']:>8.3f} |"
        f" {v['prefill_avg']:>12.2f} ± {v['prefill_std']:>8.2f} |"
        f" {v['decode_avg']:>11.2f} ± {v['decode_std']:>8.2f}"
    )
print("-" * 92)

safe = MODEL.replace(":", "_").replace("/", "_")
csv_path = os.path.join(RESULTS_DIR, f"bench_{safe}_{date.today().strftime('%Y%m%d')}.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "context_length_k",
        "ttft_avg_s", "ttft_std_s", "ttft_min_s", "ttft_max_s",
        "prefill_avg_toks_per_s", "prefill_std_toks_per_s", "prefill_min_toks_per_s", "prefill_max_toks_per_s",
        "decoding_avg_toks_per_s", "decoding_std_toks_per_s", "decoding_min_toks_per_s", "decoding_max_toks_per_s",
    ])
    for k, v in sorted(results.items()):
        w.writerow([
            k,
            v["ttft_avg"], v["ttft_std"], v["ttft_min"], v["ttft_max"],
            v["prefill_avg"], v["prefill_std"], v["prefill_min"], v["prefill_max"],
            v["decode_avg"], v["decode_std"], v["decode_min"], v["decode_max"],
        ])
print(f"\nSaved: {csv_path}")
