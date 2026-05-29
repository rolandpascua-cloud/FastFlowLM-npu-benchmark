# Technical Notes — Issues Encountered and Resolved

This document records the technical challenges hit during the benchmark run and
the solutions found. Useful context for anyone reproducing these results or
extending the work.

---

## 1. `--verbose` and `--prompt` Flags Do Not Exist

**Problem:** The initial plan used `flm run <model> --verbose --prompt "..."`.
This produced:
```
Error parsing arguments: unrecognised option '--verbose'
```

**Solution:** Switched to `flm bench <model>` for small models, and
`flm serve <model>` + OpenAI-compatible API calls for larger models.
The API `usage` field contains all timing metrics: `prefill_duration_ttft`,
`prefill_speed_tps`, `decoding_speed_tps`.

---

## 2. `flm bench` CSV Is Saved to the CWD

**Problem:** `flm bench` saves its CSV to the **current working directory**, not a
fixed path. When invoked via SSH background tasks with an unpredictable CWD, CSVs
appeared missing.

**Solution:** Always `cd` to the target results directory before invoking:
```bash
cd ~/fastflowlm-npu-benchmark/results && flm bench llama3.2:1b
```

---

## 3. Multiple Installed Models Exhaust NPU Memory

**Problem:** With several models installed simultaneously, `flm bench` failed:
```
Error: Failed to allocate xrt::ext::bo: mmap(...) failed (err=-12): Cannot allocate memory
```

**Root cause:** The system has ~10GB of NPU-accessible shared memory. The OS caches
all installed model weight files in the page cache, consuming shmem even when no
model is actively running.

**Solution:**
1. Install only one model at a time.
2. Drop the OS page cache before each benchmark:
   ```bash
   sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
   ```
3. For 4B+ models, use `flm serve --ctx-len <n>` + API calls instead of `flm bench`.

---

## 4. OOM Kill at 32k Context for 4B+ Models

**Problem:** `flm bench` begins at 32k context. For 4B+ models the kernel OOM killer
terminated the process immediately. Journal showed:
```
Out of memory: Killed process (flm) shmem-rss:10247360kB
```

The 32k KV cache for a 4B model consumed the full ~10GB shmem budget.

**Solution:** Use `flm serve <model> --ctx-len 16384` and benchmark via API at
1k–16k only. Keeps peak shmem within budget.

---

## 5. qwen3:0.6b Core Dump at 32k Context

**Problem:** `flm bench qwen3:0.6b` crashed with a C++ assertion failure in
`stl_vector::back()`. This is within memory limits for a 0.6B model — it is
a FLM bug, not an OOM.

**Solution:** Model skipped; bug reported upstream.

---

## 6. qwen3:8b Server Crash at 2k Context

**Problem:** `flm serve qwen3:8b` handled the 1k query then died (connection reset)
when a 2k prompt was submitted. By contrast, llama3.1:8b ran cleanly to 16k.

**Root cause:** The Qwen3 architecture uses a larger KV cache per token than Llama 3.1.
The 2k context pushed qwen3:8b over the shmem limit.

**Solution:** Only 1k context data collected for qwen3:8b; noted in results.

---

## 7. Accumulated OS Page Cache Between Benchmarks

**Problem:** As more models were downloaded and benchmarked, available memory shrank
even though `free -h` showed large "available" figures. Later benchmarks failed on
first attempt.

**Root cause:** The NPU driver's `mmap` requires contiguous clean pages. The OS
page cache filled with model weight files, fragmenting available memory.

**Solution:** `sync && echo 3 | sudo tee /proc/sys/vm/drop_caches` added as a
mandatory step before each benchmark.

---

## 8. Background Task Output Truncation

**Problem:** Long-running SSH commands had their local output buffer truncated at
~153 lines. The final results table and CSV write were missed; tasks reported
`exit code 0` but no CSV was found.

**Solution:**
- Always verify the CSV exists after task completion.
- Use `tee` to a persistent remote file as backup:
  ```bash
  flm bench <model> 2>&1 | tee /tmp/bench_output.txt
  ```
- For data captured only in monitor notifications, reconstruct the CSV
  manually from per-iteration log values.

---

## 9. Concurrent FLM Processes Corrupt Results

**Problem:** Multiple background tasks inadvertently launched concurrent `flm bench`
processes. Resulting CSVs had extreme variance (std dev larger than mean) and
decode speeds far below expected.

**Detection:** Corrupted results show `ttft_std > ttft_avg * 0.1` or decode speeds
implausibly low for the model size.

**Solution:** Always verify no FLM processes are running before starting a benchmark:
```bash
pgrep -a flm || echo "clear to run"
```

---

## 10. NPU vs GPU/CPU Verification

**How we confirmed NPU is doing the work:**
```bash
# Check which process holds the NPU device file open
for pid in $(pgrep flm); do
    ls -la /proc/$pid/fd 2>/dev/null | grep accel
done

# Monitor iGPU utilization during active inference
watch -n1 cat /sys/devices/pci0000:00/0000:00:08.1/0000:c4:00.0/gpu_busy_percent
```

**Results during inference:**
- `/dev/accel/accel0` held open by FLM worker process
- iGPU busy: **0%** consistently
- CPU: 0–18% (orchestration overhead only)

All inference confirmed on the XDNA2 NPU.

---

*ASUS ROG Flow Z13 · Ryzen AI Max+ 395 · XDNA2 NPU · FastFlowLM*
