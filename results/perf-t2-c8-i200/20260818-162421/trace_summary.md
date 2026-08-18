# T2: concurrency=8 interval=200ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T16:24:31+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1593** | 0.2257 | 0.2321 | [0.2014, 0.2532] | 0.1426 | 0.4378 |
| Isolated | 72 | **0.1588** | 0.3863 | 0.7831 | [0.3093, 0.4743] | 0.1438 | 0.9606 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2861** | 1.3524 | 0.2337 | [1.3276, 1.3801] | 1.2613 | 1.5663 |
| Isolated | 72 | **1.2849** | 1.5123 | 0.7888 | [1.4344, 1.6013] | 1.2653 | 2.1003 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3895s
- Isolated: n=24, median=0.9428s
- Prefill saved (median): +553.3ms
- DMA cost (per-request, bound): 151.0ms
- Per-instance median paired delta (D5): NPU0:+553.3ms, NPU1:+771.6ms, NPU2:-229.3ms, NPU3:+525.3ms, NPU4:+554.2ms, NPU5:+546.8ms, NPU6:+554.5ms, NPU7:+554.3ms
- Lifecycle cluster CI, per query class (C5): CI [476.2, 483.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1514s
- Isolated: n=24, median=0.1547s
- Prefill saved (median): +3.3ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+6.3ms, NPU1:+1.1ms, NPU2:+4.3ms, NPU3:+8.2ms, NPU4:+2.7ms, NPU5:+0.6ms, NPU6:+1.8ms, NPU7:+6.5ms
- Lifecycle cluster CI, per query class (C5): CI [3.1, 3.8]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.1594s
- Isolated: n=24, median=0.1583s
- Prefill saved (median): -1.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+2.5ms, NPU1:-2.7ms, NPU2:-8.0ms, NPU3:+1.8ms, NPU4:-3.7ms, NPU5:+1.0ms, NPU6:+2.1ms, NPU7:+4.0ms
- Lifecycle cluster CI, per query class (C5): CI [-1.9, 1.7]ms includes 0
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
- Run ID: 20260818-162421
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
- Command: `python scripts/run_perf_t2-c8-i200_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

