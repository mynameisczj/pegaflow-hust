# T2: concurrency=4 interval=200ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T15:05:07+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1546** | 0.2041 | 0.1891 | [0.1817, 0.2293] | 0.0944 | 0.4050 |
| Isolated | 72 | **0.1565** | 0.3838 | 0.7820 | [0.3066, 0.4720] | 0.1414 | 0.9647 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2791** | 1.3295 | 0.2002 | [1.3064, 1.3550] | 1.2106 | 1.5303 |
| Isolated | 72 | **1.2809** | 1.5075 | 0.7856 | [1.4297, 1.5964] | 1.2533 | 2.0910 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3607s
- Isolated: n=24, median=0.9413s
- Prefill saved (median): +580.6ms
- DMA cost (per-request, bound): 120.4ms
- Per-instance median paired delta (D5): NPU0:+592.9ms, NPU1:-180.0ms, NPU2:+582.4ms, NPU3:+627.9ms, NPU4:+562.5ms, NPU5:+572.0ms, NPU6:+608.1ms, NPU7:+577.8ms
- Lifecycle cluster CI, per query class (C5): CI [497.0, 522.5]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1506s
- Isolated: n=24, median=0.1515s
- Prefill saved (median): +0.9ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+8.5ms, NPU1:+0.1ms, NPU2:+1.9ms, NPU3:+1.1ms, NPU4:+6.9ms, NPU5:+1.7ms, NPU6:+8.7ms, NPU7:-2.3ms
- Lifecycle cluster CI, per query class (C5): CI [-0.5, 4.5]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.1458s
- Isolated: n=24, median=0.1566s
- Prefill saved (median): +10.8ms
- DMA cost (per-request, bound): 2.2ms
- Per-instance median paired delta (D5): NPU0:+57.7ms, NPU1:-1.0ms, NPU2:+60.5ms, NPU3:-0.3ms, NPU4:+49.2ms, NPU5:+0.0ms, NPU6:+56.6ms, NPU7:+60.5ms
- Lifecycle cluster CI, per query class (C5): CI [26.8, 30.6]ms excludes 0
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
- Median TTFT: 0.9343s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-150456
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
- Command: `python scripts/run_perf_t2-c4-i200_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

