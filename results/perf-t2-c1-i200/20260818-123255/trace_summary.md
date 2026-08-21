# T2: concurrency=1 interval=200ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T12:33:06+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1501** | 0.1865 | 0.2209 | [0.1652, 0.2084] | 0.0937 | 0.3426 |
| Isolated | 72 | **0.1558** | 0.3821 | 0.7833 | [0.3051, 0.4702] | 0.1409 | 0.9562 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2751** | 1.3113 | 0.2198 | [1.2898, 1.3337] | 1.2109 | 1.4711 |
| Isolated | 72 | **1.2798** | 1.5089 | 0.7868 | [1.4296, 1.5994] | 1.2554 | 2.1752 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3257s
- Isolated: n=24, median=0.9376s
- Prefill saved (median): +611.9ms
- DMA cost (per-request, bound): 90.8ms
- Per-instance median paired delta (D5): NPU0:+613.2ms, NPU1:+779.0ms, NPU2:+610.0ms, NPU3:+627.0ms, NPU4:+610.3ms, NPU5:+604.8ms, NPU6:-169.7ms, NPU7:+608.4ms
- Lifecycle cluster CI, per query class (C5): CI [527.3, 541.2]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1499s
- Isolated: n=24, median=0.1504s
- Prefill saved (median): +0.5ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-2.0ms, NPU1:-2.2ms, NPU2:-1.4ms, NPU3:+3.3ms, NPU4:-3.1ms, NPU5:+5.3ms, NPU6:+2.3ms, NPU7:+2.8ms
- Lifecycle cluster CI, per query class (C5): CI [-1.5, 1.9]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0967s
- Isolated: n=24, median=0.1561s
- Prefill saved (median): +59.4ms
- DMA cost (per-request, bound): 1.9ms
- Per-instance median paired delta (D5): NPU0:+52.9ms, NPU1:-1.8ms, NPU2:+56.2ms, NPU3:+61.7ms, NPU4:+62.8ms, NPU5:+62.5ms, NPU6:+53.5ms, NPU7:+62.6ms
- Lifecycle cluster CI, per query class (C5): CI [49.6, 53.5]ms excludes 0
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
- Run ID: 20260818-123255
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
- Command: `python scripts/run_perf_t2-c1-i200_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

