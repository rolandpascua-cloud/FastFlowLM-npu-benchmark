# FastFlowLM NPU Benchmark -- ASUS ROG Flow Z13

**Hardware:** Ryzen AI Max+ 395 (Strix Halo) · XDNA2 NPU 50 TOPS · ~30GB available RAM
**Date:** 2026-05-29  **FLM:** NPU FW 1.1.2.65 / amdxdna 0.6
**NPU power mode:** performance (default)

## Benchmark Methods

- **flm bench** (<=3B): built-in tool, 8 iterations x 6 context lengths (1k-32k tokens)
- **serve API** (>=4B): custom script, 8 iterations x 5 context lengths (1k-16k);
  32k context causes OOM at >=4B on this system's ~10GB NPU/shmem budget
- All inference verified on `/dev/accel/accel0` (XDNA2 NPU) -- GPU held at 0% throughout

---

## Quick Comparison -- 1k Context (Typical Workload)

| Model | Size | Params | TTFT (s) | Prefill (tok/s) | Decode (tok/s) | Notes |
|---|---|---|---|---|---|---|
| llama3.2:1b | ~1.2GB | 1B | 0.69 | 1467 | 57.9 |  |
| lfm2:1.2b | ~0.9GB | 1.2B | 0.64 | 1528 | 60.4 | Liquid AI |
| llama3.2:3b | ~2.7GB | 3B | 1.41 | 712 | 23.5 |  |
| nanbeige4.1:3b | ~2.9GB | 3B | 1.68 | 594 | 21.3 | 3-iter estimate |
| qwen3:4b | ~3.1GB | 4B | 7.95 | 128 | 23.9 | slow prefill on NPU |
| phi4-mini-it:4b | ~3.4GB | 4B | 1.59 | 552 | 19.7 |  |
| gemma3:4b | ~4.6GB | 4B | 1.72 | 515 | 17.4 | includes vision weights |
| qwen3:8b | ~5.7GB | 8B | 2.74 | 325 | 10.5 | 1k context only |
| llama3.1:8b | ~5.5GB | 8B | 2.82 | 323 | 11.0 |  |
| deepseek-r1:8b | ~5.5GB | 8B | 2.74 | 321 | 10.9 | reasoning/R1 distill |
| gemma4-it:e4b | ~8.7GB | eff-4B | 2.14 | 413 | 11.5 | MoE + vision + audio |
| gpt-oss:20b | ~11GB | 20B MoE | 4.72 | 219 | 19.2 |  |

---

## Full Results by Model

### llama3.2:1b  (1B, ~1.2GB)
Method: flm bench

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 0.687 | 1466.8 | 57.9 |
| 2k | 1.062 | 1860.1 | 54.7 |
| 4k | 1.960 | 1996.0 | 50.9 |
| 8k | 3.997 | 1948.1 | 43.5 |
| 16k | 9.744 | 1592.9 | 34.5 |
| 32k | 28.563 | 1085.5 | 24.2 |

### lfm2:1.2b  (1.2B, ~0.9GB)
Method: flm bench  |  Liquid AI

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 0.642 | 1528.4 | 60.4 |
| 2k | 0.985 | 1981.0 | 59.5 |
| 4k | 1.685 | 2309.0 | 58.1 |
| 8k | 3.167 | 2455.1 | 54.0 |
| 16k | 6.747 | 2300.0 | 46.5 |
| 32k | 16.678 | 1860.2 | 37.9 |

### llama3.2:3b  (3B, ~2.7GB)
Method: flm bench

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 1.412 | 711.9 | 23.5 |
| 2k | 2.230 | 884.4 | 22.1 |
| 4k | 4.193 | 948.2 | 20.4 |
| 8k | 7.233 | 1099.5 | 19.0 |
| 16k | 14.648 | 2180.1 | 37.0 |
| 32k | 29.812 | 2138.6 | 33.4 |

### nanbeige4.1:3b  (3B, ~2.9GB)
Method: flm bench  |  3-iter estimate

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 1.684 | 594.0 | 21.3 |
| 2k | 2.845 | 692.4 | 20.3 |
| 4k | 5.406 | 722.6 | 18.7 |
| 8k | 11.608 | 669.9 | 16.0 |
| 16k | 29.778 | 521.4 | 12.5 |
| 32k | 90.581 | 342.4 | 8.7 |

### qwen3:4b  (4B, ~3.1GB)
Method: serve API  |  slow prefill on NPU

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 7.950 | 128.3 | 23.9 |
| 2k | 16.008 | 127.9 | 23.0 |
| 4k | 31.922 | 129.1 | 21.8 |
| 8k | 63.893 | 128.9 | 20.4 |
| 16k | 127.840 | 128.9 | 18.5 |
| 32k | -- | -- | -- |

### phi4-mini-it:4b  (4B, ~3.4GB)
Method: serve API

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 1.594 | 552.0 | 19.7 |
| 2k | 2.322 | 770.5 | 18.9 |
| 4k | 4.456 | 809.8 | 17.3 |
| 8k | 9.584 | 722.2 | 15.1 |
| 16k | 16.234 | 647.6 | 13.2 |
| 32k | -- | -- | -- |

### gemma3:4b  (4B, ~4.6GB)
Method: serve API  |  includes vision weights

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 1.716 | 515.3 | 17.4 |
| 2k | 2.748 | 652.5 | 17.2 |
| 4k | 4.451 | 811.7 | 16.9 |
| 8k | 8.606 | 804.9 | 16.6 |
| 16k | 13.049 | 806.0 | 16.2 |
| 32k | -- | -- | -- |

### qwen3:8b  (8B, ~5.7GB)
Method: serve API  |  1k context only

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 2.735 | 324.7 | 10.5 |
| 2k | -- | -- | -- |
| 4k | -- | -- | -- |
| 8k | -- | -- | -- |
| 16k | -- | -- | -- |
| 32k | -- | -- | -- |

### llama3.1:8b  (8B, ~5.5GB)
Method: serve API

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 2.821 | 322.6 | 11.0 |
| 2k | 4.528 | 401.9 | 10.7 |
| 4k | 7.916 | 459.9 | 10.2 |
| 8k | 16.493 | 421.6 | 9.3 |
| 16k | 27.171 | 388.1 | 8.6 |
| 32k | -- | -- | -- |

### deepseek-r1:8b  (8B, ~5.5GB)
Method: serve API  |  reasoning/R1 distill

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 2.742 | 320.6 | 10.9 |
| 2k | 4.072 | 439.4 | 10.7 |
| 4k | 7.853 | 459.7 | 10.1 |
| 8k | 16.396 | 422.2 | 9.3 |
| 16k | 27.001 | 389.4 | 8.6 |
| 32k | -- | -- | -- |

### gemma4-it:e4b  (eff-4B, ~8.7GB)
Method: serve API  |  MoE + vision + audio

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 2.137 | 413.3 | 11.5 |
| 2k | 3.378 | 530.8 | 11.3 |
| 4k | 5.640 | 640.6 | 10.8 |
| 8k | 11.137 | 622.0 | 10.0 |
| 16k | 17.497 | 601.1 | 9.3 |
| 32k | -- | -- | -- |

### gpt-oss:20b  (20B MoE, ~11GB)
Method: flm bench

| Context | TTFT (s) | Prefill (tok/s) | Decode (tok/s) |
|---|---|---|---|
| 1k | 4.719 | 219.5 | 19.2 |
| 2k | 6.174 | 324.7 | 18.9 |
| 4k | 9.386 | 420.0 | 18.2 |
| 8k | 16.338 | 478.4 | 17.0 |
| 16k | 33.370 | 466.3 | 15.1 |
| 32k | 80.878 | 384.0 | 12.4 |

---

## Key Findings

### 1. NPU Utilization Confirmed
All models run exclusively on `/dev/accel/accel0` (XDNA2 NPU).
The AMD Radeon GPU (`amdgpu`) held at **0%** throughout all inference.
CPU usage during inference: ~0-18% (orchestration/host overhead only).

### 2. Speed Champion: lfm2:1.2b (Liquid AI)
**60.4 tok/s** decode at 1k context, maintaining **37.9 tok/s** at 32k.
Best decode throughput and best decode/context-length retention of any model tested.
Also the smallest model at ~0.9GB.

### 3. Anomalous llama3.2:3b Behavior -- Decode Accelerates at Long Context
Decode speed *increases* above 8k context: 19 tok/s at 8k rising to **37 tok/s at 16k**.
FLM appears to switch to a more efficient NPU kernel tiling strategy at a context threshold.
At 32k, the 3B model (33.4 tok/s) outperforms the 1B model (24.2 tok/s).

### 4. Memory Constraint: ~10GB NPU/shmem Budget
Available NPU shared memory: ~10GB for model weights + KV cache combined.
- **<=3B models**: 32k context feasible (flm bench works fully)
- **4B models**: 16k context max via serve mode; 32k OOMs
- **8B models**: 16k viable for most; qwen3:8b crashed at 2k (architecture-dependent)
Workaround: drop OS page cache (`echo 3 > /proc/sys/vm/drop_caches`) before each benchmark.

### 5. Best 4B Model: phi4-mini-it:4b
**19.7 tok/s** decode at 1k context -- highest of any 4B model tested.
Strong prefill at 4k+ (~810 tok/s). Consistent across all context lengths.

### 6. 8B Model Decode Floor: ~10-11 tok/s
All three 8B models (llama3.1, deepseek-r1, qwen3) cluster at 10-11 tok/s at 1k,
dropping to ~8.6 tok/s at 16k. llama3.1:8b and deepseek-r1:8b are essentially identical.

### 7. qwen3:4b -- Anomalously Slow Prefill
Prefill measured at **128 tok/s** vs 500-810 tok/s for other 4B models.
Decode (23.9 tok/s) is in line with the family, suggesting the architecture is
not well-matched to the XDNA2 prefill path. Needs re-verification.

### 8. gpt-oss:20b -- MoE Efficiency Loss on XDNA2
Despite 20B parameters, decode is only **19.2 tok/s** -- comparable to 4B models.
Prefill at 1k (219 tok/s) is the lowest of any model. MoE routing overhead
is not amortized efficiently on the XDNA2's fixed-function NPU columns.

---
*Generated 2026-05-29 · FastFlowLM NPU Benchmark Suite*
