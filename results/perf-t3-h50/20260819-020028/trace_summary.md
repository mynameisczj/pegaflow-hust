# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `8d84c36ffae9` (parent: `35af07ac0996`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T02:00:38+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.2097** | 0.2409 | 0.2543 | [0.2060, 0.2785] | 0.0934 | 0.8291 |
| Isolated | 72 | **0.5338** | 0.6211 | 1.1162 | [0.5192, 0.7275] | 0.1445 | 1.2979 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.3379** | 1.3750 | 0.2779 | [1.3372, 1.4150] | 1.2058 | 1.9856 |
| Isolated | 72 | **1.6626** | 1.7544 | 1.1407 | [1.6502, 1.8641] | 1.2599 | 2.4519 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3581s
- Isolated: n=24, median=1.2770s
- Prefill saved (median): +918.9ms
- DMA cost (per-request, bound): 116.5ms
- Per-instance median paired delta (D5): NPU0:+914.9ms, NPU1:+914.0ms, NPU2:+477.0ms, NPU3:+925.8ms, NPU4:+911.5ms, NPU5:+921.1ms, NPU6:+927.9ms, NPU7:+909.6ms
- Lifecycle cluster CI, per query class (C5): CI [804.2, 811.6]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.2098s
- Isolated: n=24, median=0.5338s
- Prefill saved (median): +324.0ms
- DMA cost (per-request, bound): 45.5ms
- Per-instance median paired delta (D5): NPU0:+323.9ms, NPU1:+316.6ms, NPU2:+327.1ms, NPU3:+334.4ms, NPU4:+312.5ms, NPU5:+330.0ms, NPU6:+322.0ms, NPU7:+317.5ms
- Lifecycle cluster CI, per query class (C5): CI [275.6, 287.4]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q2
- Shared: n=24, median=0.0965s
- Isolated: n=24, median=0.1542s
- Prefill saved (median): +57.7ms
- DMA cost (per-request, bound): 1.9ms
- Per-instance median paired delta (D5): NPU0:+55.8ms, NPU1:+60.9ms, NPU2:+50.2ms, NPU3:+58.5ms, NPU4:+59.3ms, NPU5:+51.2ms, NPU6:+58.6ms, NPU7:+53.1ms
- Lifecycle cluster CI, per query class (C5): CI [49.6, 51.4]ms excludes 0
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
- Median TTFT: 0.9342s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] T3 gate FAILED: measured hit rate 114.0% vs target 50% (deviation > 5pp)

## Validity Manifest
- Run ID: 20260819-020028
- Total records: 150
- Consumer shared records: 72
- Consumer isolated records: 72
- Producer records: 6
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: FAIL
- Audit verdict: INVALID

## Reproduce
- Command: `python scripts/run_perf_t3-h50_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

