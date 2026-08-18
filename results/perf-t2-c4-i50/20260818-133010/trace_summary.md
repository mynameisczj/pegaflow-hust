# T2: concurrency=4 interval=50ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T13:30:21+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1551** | 0.2050 | 0.1962 | [0.1825, 0.2300] | 0.0936 | 0.4095 |
| Isolated | 72 | **0.1568** | 0.3847 | 0.7846 | [0.3075, 0.4728] | 0.1471 | 0.9567 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2795** | 1.3309 | 0.2015 | [1.3081, 1.3564] | 1.2121 | 1.5400 |
| Isolated | 72 | **1.2828** | 1.5096 | 0.7890 | [1.4316, 1.5986] | 1.2604 | 2.0895 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3642s
- Isolated: n=24, median=0.9415s
- Prefill saved (median): +577.3ms
- DMA cost (per-request, bound): 120.9ms
- Per-instance median paired delta (D5): NPU0:+586.1ms, NPU1:-215.1ms, NPU2:+575.1ms, NPU3:+572.6ms, NPU4:+591.1ms, NPU5:+608.3ms, NPU6:+599.2ms, NPU7:+585.6ms
- Lifecycle cluster CI, per query class (C5): CI [497.3, 517.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1517s
- Isolated: n=24, median=0.1539s
- Prefill saved (median): +2.2ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+1.0ms, NPU1:+0.4ms, NPU2:+1.5ms, NPU3:+3.9ms, NPU4:-0.7ms, NPU5:+1.6ms, NPU6:+3.5ms, NPU7:-5.0ms
- Lifecycle cluster CI, per query class (C5): CI [-1.9, 3.7]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.1511s
- Isolated: n=24, median=0.1570s
- Prefill saved (median): +5.9ms
- DMA cost (per-request, bound): 1.9ms
- Per-instance median paired delta (D5): NPU0:+0.3ms, NPU1:+62.5ms, NPU2:+50.2ms, NPU3:+51.1ms, NPU4:+55.2ms, NPU5:-0.8ms, NPU6:-2.5ms, NPU7:+59.9ms
- Lifecycle cluster CI, per query class (C5): CI [28.5, 31.8]ms excludes 0
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
- Median TTFT: 0.9347s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] NPU6 owner drift: foreign pid=21940 attached to admitted device

## Validity Manifest
- Run ID: 20260818-133010
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
- Command: `python scripts/run_perf_t2-c4-i50_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

