# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `56ad3c426adb` (parent: `c3582fcbb855`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T03:17:06+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.6532** | 0.6398 | 0.0056 | [0.6101, 0.6558] | 0.5372 | 0.6582 |
| Isolated | 8 | **0.9427** | 0.8931 | 0.0102 | [0.7895, 0.9476] | 0.5328 | 0.9533 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.7825** | 1.7664 | 0.0074 | [1.7355, 1.7841] | 1.6588 | 1.7873 |
| Isolated | 8 | **2.0709** | 2.0220 | 0.0193 | [1.9195, 2.0774] | 1.6656 | 2.0834 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.6535s
- Isolated: n=8, median=0.9435s
- Prefill saved (median): +290.0ms
- DMA cost (per-request, bound): 47.0ms
- Per-instance median paired delta (D5): NPU0:+280.6ms, NPU1:-120.0ms, NPU2:+403.5ms, NPU3:+298.4ms, NPU4:+290.0ms, NPU5:+295.1ms, NPU6:+290.4ms, NPU7:+288.5ms
- Lifecycle cluster CI, per query class (C5): CI [253.3, 253.3]ms excludes 0
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
- Count: 2
- Median TTFT: 0.9409s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] T3 gate FAILED: measured hit rate 42.3% vs target 50% (deviation > 5pp)

## Validity Manifest
- Run ID: 20260819-031656
- Total records: 18
- Consumer shared records: 8
- Consumer isolated records: 8
- Producer records: 2
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: FAIL
- Audit verdict: INVALID

## Reproduce
- Command: `python scripts/run_perf_t3-h50_baseline.py --cycles 1 --requests-per-phase 1 --pool-size 16gb --num-instances 8`

