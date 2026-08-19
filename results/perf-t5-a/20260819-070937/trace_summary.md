# T5 combo a: gmu=0.85 external=False Summary

## Environment
- Commit: `7c4b7323f0d1` (parent: `54e132aeb68a`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T07:09:48+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **0.1504** | 0.1786 | 0.1741 | [0.1516, 0.2093] | 0.0932 | 0.3393 |
| Isolated | 36 | **0.1529** | 0.3452 | 0.7815 | [0.2359, 0.4562] | 0.1360 | 0.9495 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **1.2793** | 1.3054 | 0.1857 | [1.2773, 1.3362] | 1.2096 | 1.4709 |
| Isolated | 36 | **1.2770** | 1.4683 | 0.7870 | [1.3580, 1.5806] | 1.2523 | 2.0813 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=12, median=0.3176s
- Isolated: n=12, median=0.9316s
- Prefill saved (median): +614.0ms
- DMA cost (per-request, bound): 89.2ms
- Per-instance median paired delta (D5): NPU0:+613.6ms, NPU1:+624.5ms, NPU2:+622.2ms, NPU3:+628.0ms
- Lifecycle cluster CI, per query class (C5): CI [456.3, 463.2]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=12, median=0.1507s
- Isolated: n=12, median=0.1492s
- Prefill saved (median): -1.5ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+1.2ms, NPU1:-1.4ms, NPU2:-2.5ms, NPU3:-5.0ms
- Lifecycle cluster CI, per query class (C5): CI [-2.4, 0.5]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=12, median=0.0975s
- Isolated: n=12, median=0.1518s
- Prefill saved (median): +54.3ms
- DMA cost (per-request, bound): 1.8ms
- Per-instance median paired delta (D5): NPU0:+51.1ms, NPU1:+61.0ms, NPU2:+47.0ms, NPU3:+56.9ms
- Lifecycle cluster CI, per query class (C5): CI [36.1, 44.4]ms excludes 0
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
- Median TTFT: 0.9357s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-070937
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
- Command: `python scripts/run_perf_t5-a_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 4`

