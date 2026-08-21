# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `5b992ea07376` (parent: `7478c535e314`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T02:53:34+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.1059** | 1.0920 | 0.0109 | [1.0587, 1.1120] | 0.9783 | 1.1205 |
| Isolated | 8 | **1.3846** | 1.3390 | 0.0168 | [1.2358, 1.3950] | 0.9819 | 1.4070 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **2.2698** | 2.2562 | 0.0149 | [2.2249, 2.2757] | 2.1480 | 2.2817 |
| Isolated | 8 | **2.5439** | 2.4999 | 0.0161 | [2.3990, 2.5555] | 2.1509 | 2.5693 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=1.1079s
- Isolated: n=8, median=1.3855s
- Prefill saved (median): +277.6ms
- DMA cost (per-request, bound): 50.1ms
- Per-instance median paired delta (D5): NPU0:+270.8ms, NPU1:-122.0ms, NPU2:+282.6ms, NPU3:+285.2ms, NPU4:+286.5ms, NPU5:+283.5ms, NPU6:+405.5ms, NPU7:+283.5ms
- Lifecycle cluster CI, per query class (C5): CI [246.9, 246.9]ms excludes 0
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
- Median TTFT: 0.9328s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] T3 gate FAILED: measured hit rate 30.3% vs target 50% (deviation > 5pp)

## Validity Manifest
- Run ID: 20260819-025323
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

