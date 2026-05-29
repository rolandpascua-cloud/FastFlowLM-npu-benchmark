# FastFlowLM NPU Benchmark

**Benchmarking LLM inference on the AMD XDNA2 NPU** using
[FastFlowLM](https://github.com/amd/fastflowlm) on the ASUS ROG Flow Z13
(Ryzen AI Max+ 395 / Strix Halo).

This repository contains benchmark scripts, raw CSV results, and analysis
for 12 models ranging from 1B to 20B parameters, all running **entirely on
the NPU** — no GPU, no CPU compute.

---

## Hardware

| Component | Detail |
|---|---|
| Machine | ASUS ROG Flow Z13 |
| CPU | AMD Ryzen AI Max+ 395 (Strix Halo, 16c/32t) |
| NPU | AMD XDNA2, 50 TOPS, 8 columns |
| NPU FW | 1.1.2.65 |
| amdxdna driver | 0.6 |
| OS | Fedora 43, kernel 7.0.7-100.fc43.x86_64 |
| RAM | ~30GB available to OS (unified memory) |
| FLM | FastFlowLM (validated via `flm validate`) |

---

## Results Summary (1k Context)

| Model | Size | Params | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|---|---|
| lfm2:1.2b | ~0.9GB | 1.2B | 0.64 | 1528 | **60.4** |
| llama3.2:1b | ~1.2GB | 1B | 0.69 | 1467 | 57.9 |
| llama3.2:3b | ~2.7GB | 3B | 1.41 | 712 | 23.5 |
| nanbeige4.1:3b | ~2.9GB | 3B | 1.68 | 594 | 21.3 |
| phi4-mini-it:4b | ~3.4GB | 4B | **1.59** | 552 | 19.7 |
| gemma3:4b | ~4.6GB | 4B | 1.72 | 515 | 17.4 |
| qwen3:4b | ~3.1GB | 4B | 7.95 | 128 | 23.9 |
| gemma4-it:e4b | ~8.7GB | eff-4B | 2.14 | 413 | 11.5 |
| deepseek-r1:8b | ~5.5GB | 8B | 2.74 | 321 | 10.9 |
| qwen3:8b | ~5.7GB | 8B | 2.74 | 325 | 10.5 |
| llama3.1:8b | ~5.5GB | 8B | 2.82 | 323 | 11.0 |
| gpt-oss:20b | ~11GB | 20B MoE | 4.72 | 219 | 19.2 |

Full results with all context lengths (1k–32k): see [`results/SUMMARY.md`](results/SUMMARY.md).

---

## Key Findings

- **All inference runs on the NPU.** iGPU held at 0% throughout. Confirmed via
  `/dev/accel/accel0` device handle and `gpu_busy_percent` sysfs.
- **lfm2:1.2b** (Liquid AI) is the speed champion: 60 tok/s decode, retaining 38 tok/s
  at 32k context.
- **llama3.2:3b** exhibits anomalous behavior: decode speed *increases* at 16k+ context
  (23 → 37 tok/s), suggesting FLM switches NPU kernel strategies at a context threshold.
- **~10GB NPU/shmem budget**: limits ≥4B models to 16k context max, and some 8B models
  to even less.
- **phi4-mini-it:4b** is the best 4B model at 19.7 tok/s decode.
- **gpt-oss:20b** (20B MoE) delivers only 19 tok/s — similar to 4B models — suggesting
  MoE routing is not efficiently mapped to the XDNA2 fixed-function columns.

---

## Repository Structure

```
fastflowlm-npu-benchmark/
├── README.md                  — This file
├── TECHNICAL_NOTES.md         — Issues hit and solutions found
├── results/
│   ├── SUMMARY.md             — Full comparison table + analysis
│   └── bench_<model>_<date>.csv   — Raw per-iteration data (12 models)
└── scripts/
    ├── run_benchmark.sh       — Run flm bench for a single <=3B model
    ├── bench_serve.py         — Serve-based benchmark for 4B+ models
    └── gen_summary.py         — Regenerate SUMMARY.md from CSVs
```

---

## Reproducing the Benchmarks

### Prerequisites

1. XDNA2-capable AMD system with FastFlowLM installed and validated:
   ```bash
   flm validate
   ```
2. Python 3.8+ (standard library only, no pip dependencies for scripts).
3. `sudo` access to drop page cache between benchmarks.

### For models ≤3B (full 1k–32k range)

```bash
# Drop page cache first to prevent OOM
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# Run benchmark (saves CSV to current directory)
cd results/
flm bench llama3.2:1b
```

### For models ≥4B (1k–16k range, 32k OOMs on ~10GB shmem systems)

```bash
# Drop page cache first
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# Run serve-based benchmark
python3 scripts/bench_serve.py phi4-mini-it:4b
```

### Regenerate the summary table

```bash
python3 scripts/gen_summary.py ./results
```

---

## Known Limitations

| Model | Issue |
|---|---|
| qwen3:0.6b | Core dump at 32k context (FLM bug) — skipped |
| qwen3:4b | Prefill ~128 tok/s vs 500+ for other 4B models — needs re-verification |
| qwen3:8b | Only 1k context data (server crashes at 2k) |
| nanbeige4.1:3b | Results from 3 iterations rather than the standard 8 |
| All ≥4B models | No 32k data — OOM on ~10GB shmem systems |

---

## License

Benchmark scripts: MIT.
Model weights are property of their respective owners and are subject to
their individual licenses.

---

*Benchmarked 2026-05-28 · ASUS ROG Flow Z13 · AMD Ryzen AI Max+ 395 · XDNA2 NPU*
