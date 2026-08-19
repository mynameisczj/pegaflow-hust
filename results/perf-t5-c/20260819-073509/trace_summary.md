# T5 combo c: gmu=0.95 external=False Summary

## Environment
- Commit: `7c4b7323f0d1` (parent: `54e132aeb68a`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T07:35:19+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **0.1464** | 0.1772 | 0.1501 | [0.1507, 0.2072] | 0.0942 | 0.3354 |
| Isolated | 36 | **0.1542** | 0.3458 | 0.7809 | [0.2370, 0.4561] | 0.1388 | 0.9403 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **1.2667** | 1.2975 | 0.1673 | [1.2705, 1.3284] | 1.2045 | 1.4633 |
| Isolated | 36 | **1.2752** | 1.4665 | 0.7864 | [1.3568, 1.5783] | 1.2523 | 2.0645 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=12, median=0.3172s
- Isolated: n=12, median=0.9341s
- Prefill saved (median): +616.9ms
- DMA cost (per-request, bound): 88.0ms
- Per-instance median paired delta (D5): NPU0:+611.4ms, NPU1:+596.0ms, NPU2:+615.7ms, NPU3:-11.0ms
- Lifecycle cluster CI, per query class (C5): CI [454.9, 466.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=12, median=0.1470s
- Isolated: n=12, median=0.1481s
- Prefill saved (median): +1.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+4.9ms, NPU1:+5.8ms, NPU2:-2.1ms, NPU3:+4.4ms
- Lifecycle cluster CI, per query class (C5): CI [-0.3, 4.1]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=12, median=0.0981s
- Isolated: n=12, median=0.1540s
- Prefill saved (median): +55.9ms
- DMA cost (per-request, bound): 2.0ms
- Per-instance median paired delta (D5): NPU0:+49.4ms, NPU1:+48.5ms, NPU2:+60.3ms, NPU3:+50.1ms
- Lifecycle cluster CI, per query class (C5): CI [39.4, 44.3]ms excludes 0
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
- Median TTFT: 0.9323s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-073509
- Total records: 78
- Consumer shared records: 36
- Consumer isolated records: 36
- Producer records: 6
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: PASS
- Audit verdict: VALID

## Reproduce
- Command: `python scripts/run_perf_t5-c_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 4`

