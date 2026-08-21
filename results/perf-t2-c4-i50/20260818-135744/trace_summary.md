# T2: concurrency=4 interval=50ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T13:57:55+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1561** | 0.2068 | 0.1933 | [0.1837, 0.2324] | 0.0938 | 0.4151 |
| Isolated | 72 | **0.1577** | 0.3835 | 0.7833 | [0.3065, 0.4713] | 0.1421 | 0.9495 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2837** | 1.3360 | 0.1972 | [1.3124, 1.3609] | 1.2110 | 1.5439 |
| Isolated | 72 | **1.2822** | 1.5077 | 0.7861 | [1.4299, 1.5965] | 1.2615 | 2.0791 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3651s
- Isolated: n=24, median=0.9396s
- Prefill saved (median): +574.5ms
- DMA cost (per-request, bound): 123.5ms
- Per-instance median paired delta (D5): NPU0:+564.2ms, NPU1:+767.0ms, NPU2:+564.2ms, NPU3:+604.6ms, NPU4:+533.7ms, NPU5:+551.5ms, NPU6:+579.0ms, NPU7:+556.6ms
- Lifecycle cluster CI, per query class (C5): CI [488.2, 508.4]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1522s
- Isolated: n=24, median=0.1509s
- Prefill saved (median): -1.3ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-1.7ms, NPU1:-3.6ms, NPU2:-3.2ms, NPU3:+4.0ms, NPU4:+5.9ms, NPU5:-3.9ms, NPU6:+12.2ms, NPU7:-6.0ms
- Lifecycle cluster CI, per query class (C5): CI [-4.2, 3.6]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.1467s
- Isolated: n=24, median=0.1571s
- Prefill saved (median): +10.4ms
- DMA cost (per-request, bound): 2.0ms
- Per-instance median paired delta (D5): NPU0:+53.5ms, NPU1:-0.1ms, NPU2:+59.3ms, NPU3:+7.5ms, NPU4:+55.8ms, NPU5:-3.8ms, NPU6:+60.6ms, NPU7:+56.2ms
- Lifecycle cluster CI, per query class (C5): CI [28.9, 31.9]ms excludes 0
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
- Median TTFT: 0.9336s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-135744
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
- Command: `python scripts/run_perf_t2-c4-i50_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

