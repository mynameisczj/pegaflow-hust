# T2: concurrency=8 interval=50ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T15:58:15+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1585** | 0.2234 | 0.2199 | [0.1997, 0.2500] | 0.1433 | 0.4552 |
| Isolated | 72 | **0.1594** | 0.3855 | 0.7862 | [0.3084, 0.4736] | 0.1416 | 0.9532 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2849** | 1.3497 | 0.2271 | [1.3255, 1.3769] | 1.2618 | 1.5829 |
| Isolated | 72 | **1.2854** | 1.5108 | 0.7880 | [1.4331, 1.5996] | 1.2608 | 2.0855 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3845s
- Isolated: n=24, median=0.9416s
- Prefill saved (median): +557.1ms
- DMA cost (per-request, bound): 145.6ms
- Per-instance median paired delta (D5): NPU0:+565.6ms, NPU1:+774.1ms, NPU2:+497.5ms, NPU3:-208.2ms, NPU4:+556.9ms, NPU5:+548.1ms, NPU6:+561.6ms, NPU7:+552.7ms
- Lifecycle cluster CI, per query class (C5): CI [479.0, 492.6]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1528s
- Isolated: n=24, median=0.1530s
- Prefill saved (median): +0.2ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-0.4ms, NPU1:+0.2ms, NPU2:-1.7ms, NPU3:+3.9ms, NPU4:-0.6ms, NPU5:+6.0ms, NPU6:-1.7ms, NPU7:+2.9ms
- Lifecycle cluster CI, per query class (C5): CI [0.9, 1.7]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.1585s
- Isolated: n=24, median=0.1597s
- Prefill saved (median): +1.2ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+1.6ms, NPU1:-7.0ms, NPU2:+0.3ms, NPU3:+1.0ms, NPU4:-0.3ms, NPU5:+4.3ms, NPU6:-2.1ms, NPU7:+4.1ms
- Lifecycle cluster CI, per query class (C5): CI [-1.0, 1.5]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

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
- Median TTFT: 0.9396s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-155804
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
- Command: `python scripts/run_perf_t2-c8-i50_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

