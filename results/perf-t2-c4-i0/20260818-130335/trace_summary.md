# T2: concurrency=4 interval=0ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T13:03:45+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1530** | 0.2047 | 0.1901 | [0.1819, 0.2299] | 0.0926 | 0.4089 |
| Isolated | 72 | **0.1568** | 0.3837 | 0.7851 | [0.3063, 0.4720] | 0.1403 | 0.9506 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2791** | 1.3300 | 0.1961 | [1.3065, 1.3557] | 1.2074 | 1.5438 |
| Isolated | 72 | **1.2819** | 1.5086 | 0.7872 | [1.4306, 1.5977] | 1.2535 | 2.0865 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3669s
- Isolated: n=24, median=0.9424s
- Prefill saved (median): +575.5ms
- DMA cost (per-request, bound): 122.9ms
- Per-instance median paired delta (D5): NPU0:+581.6ms, NPU1:+578.1ms, NPU2:+562.5ms, NPU3:+572.0ms, NPU4:+571.6ms, NPU5:+565.2ms, NPU6:+581.7ms, NPU7:+589.5ms
- Lifecycle cluster CI, per query class (C5): CI [495.9, 517.4]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1514s
- Isolated: n=24, median=0.1520s
- Prefill saved (median): +0.6ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+2.8ms, NPU1:+0.0ms, NPU2:+2.9ms, NPU3:+1.6ms, NPU4:+0.0ms, NPU5:-0.7ms, NPU6:-1.3ms, NPU7:-1.0ms
- Lifecycle cluster CI, per query class (C5): CI [-0.2, 0.2]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.1492s
- Isolated: n=24, median=0.1571s
- Prefill saved (median): +7.9ms
- DMA cost (per-request, bound): 2.1ms
- Per-instance median paired delta (D5): NPU0:+4.2ms, NPU1:-3.2ms, NPU2:+69.1ms, NPU3:+2.0ms, NPU4:+49.8ms, NPU5:+57.4ms, NPU6:+58.3ms, NPU7:+2.6ms
- Lifecycle cluster CI, per query class (C5): CI [28.1, 33.9]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

## Negative Examples (Preserved)

### burst_concurrent_8inst
- Shared avg TTFT: 2.7s
- Isolated avg TTFT: 1.73s
- Result: +56% (shared WORSE)
- Root cause: 8 concurrent DMA streams saturate PCIe uplink
- Verdict: Burst is unrealistic workload; staggered/normal serving load unaffected

### mla_tp8_deepseek_v2_lite
- Shared avg TTFT: 0.184s
- Isolated avg TTFT: 0.187s
- Result: +1.6% (no meaningful gain)
- Root cause: MLA kv_lora_rank=512 compresses KV compute to ~100ms; DMA of compressed KV ~3ms
- Verdict: PegaFlow requires large enough prefill gap to overcome DMA cost

## Producer (Warmup Seed) Records
- Count: 6
- Median TTFT: 0.9355s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-130335
- Total records: 150
- Consumer shared records: 72
- Consumer isolated records: 72
- Producer records: 6
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: PASS
- Audit verdict: VALID

## Reproduce
- Command: `python scripts/run_perf_t2-c4-i0_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

