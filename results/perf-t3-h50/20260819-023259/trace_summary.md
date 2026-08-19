# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `7f7174788833` (parent: `8d84c36ffae9`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T02:33:10+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.3571** | 0.4164 | 0.0247 | [0.3523, 0.5390] | 0.3438 | 0.8350 |
| Isolated | 8 | **1.2814** | 1.2262 | 0.0137 | [1.1098, 1.2881] | 0.8212 | 1.2964 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.5082** | 1.5689 | 0.0286 | [1.5042, 1.6933] | 1.5003 | 1.9915 |
| Isolated | 8 | **2.4325** | 2.3765 | 0.0207 | [2.2609, 2.4389] | 1.9749 | 2.4440 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.3580s
- Isolated: n=8, median=1.2843s
- Prefill saved (median): +926.3ms
- DMA cost (per-request, bound): 118.5ms
- Per-instance median paired delta (D5): NPU0:+920.9ms, NPU1:+477.4ms, NPU2:+930.4ms, NPU3:+931.2ms, NPU4:+461.4ms, NPU5:+930.0ms, NPU6:+919.9ms, NPU7:+906.8ms
- Lifecycle cluster CI, per query class (C5): CI [809.7, 809.7]ms excludes 0
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
- Median TTFT: 0.9390s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] T3 gate FAILED: measured hit rate 114.0% vs target 50% (deviation > 5pp)

## Validity Manifest
- Run ID: 20260819-023259
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

