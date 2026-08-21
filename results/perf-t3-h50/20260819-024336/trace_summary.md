# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `7478c535e314` (parent: `7f7174788833`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T02:43:47+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.1045** | 1.0933 | 0.0209 | [1.0625, 1.1137] | 0.9903 | 1.1234 |
| Isolated | 8 | **1.3872** | 1.3415 | 0.0147 | [1.2406, 1.3955] | 0.9916 | 1.4033 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **2.2676** | 2.2577 | 0.0233 | [2.2279, 2.2779] | 2.1586 | 2.2886 |
| Isolated | 8 | **2.5525** | 2.5065 | 0.0181 | [2.4063, 2.5607] | 2.1588 | 2.5678 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=1.1048s
- Isolated: n=8, median=1.3875s
- Prefill saved (median): +282.7ms
- DMA cost (per-request, bound): 46.7ms
- Per-instance median paired delta (D5): NPU0:+272.0ms, NPU1:-113.2ms, NPU2:+396.1ms, NPU3:+282.1ms, NPU4:+277.7ms, NPU5:+295.4ms, NPU6:+286.5ms, NPU7:+289.0ms
- Lifecycle cluster CI, per query class (C5): CI [248.2, 248.2]ms excludes 0
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
- Median TTFT: 0.9461s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] T3 gate FAILED: measured hit rate 43.8% vs target 50% (deviation > 5pp)

## Validity Manifest
- Run ID: 20260819-024336
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

