# T2: concurrency=1 interval=50ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T11:49:43+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1508** | 0.1861 | 0.2177 | [0.1650, 0.2078] | 0.0945 | 0.3454 |
| Isolated | 72 | **0.1557** | 0.3829 | 0.7856 | [0.3059, 0.4708] | 0.1472 | 0.9495 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2751** | 1.3110 | 0.2213 | [1.2895, 1.3332] | 1.2067 | 1.4757 |
| Isolated | 72 | **1.2790** | 1.5082 | 0.7881 | [1.4303, 1.5969] | 1.2687 | 2.0819 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3224s
- Isolated: n=24, median=0.9391s
- Prefill saved (median): +616.7ms
- DMA cost (per-request, bound): 89.3ms
- Per-instance median paired delta (D5): NPU0:+624.1ms, NPU1:+620.8ms, NPU2:+613.7ms, NPU3:+634.0ms, NPU4:+618.9ms, NPU5:+611.6ms, NPU6:+610.2ms, NPU7:+598.7ms
- Lifecycle cluster CI, per query class (C5): CI [537.1, 538.9]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1504s
- Isolated: n=24, median=0.1504s
- Prefill saved (median): +0.0ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+3.1ms, NPU1:+4.1ms, NPU2:+0.5ms, NPU3:+4.0ms, NPU4:+0.1ms, NPU5:+0.9ms, NPU6:-1.9ms, NPU7:+3.4ms
- Lifecycle cluster CI, per query class (C5): CI [0.9, 1.4]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0972s
- Isolated: n=24, median=0.1560s
- Prefill saved (median): +58.8ms
- DMA cost (per-request, bound): 2.0ms
- Per-instance median paired delta (D5): NPU0:+56.3ms, NPU1:+51.3ms, NPU2:+58.7ms, NPU3:+58.4ms, NPU4:+60.4ms, NPU5:+57.1ms, NPU6:+57.6ms, NPU7:+60.0ms
- Lifecycle cluster CI, per query class (C5): CI [49.7, 52.1]ms excludes 0
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
- Median TTFT: 0.9371s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-114932
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
- Command: `python scripts/run_perf_t2-c1-i50_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

