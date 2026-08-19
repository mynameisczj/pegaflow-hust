# T5 combo d: gmu=0.95 external=True Summary

## Environment
- Commit: `7c4b7323f0d1` (parent: `54e132aeb68a`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T08:35:51+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **0.1538** | 0.1844 | 0.1696 | [0.1577, 0.2150] | 0.1006 | 0.3496 |
| Isolated | 36 | **0.1582** | 0.3543 | 0.7829 | [0.2444, 0.4655] | 0.1445 | 0.9609 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **1.2708** | 1.3059 | 0.1769 | [1.2774, 1.3376] | 1.2096 | 1.4755 |
| Isolated | 36 | **1.2841** | 1.4728 | 0.7885 | [1.3627, 1.5850] | 1.2526 | 2.0799 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=12, median=0.3242s
- Isolated: n=12, median=0.9436s
- Prefill saved (median): +619.4ms
- DMA cost (per-request, bound): 88.4ms
- Per-instance median paired delta (D5): NPU0:+617.1ms, NPU1:+594.0ms, NPU2:+628.0ms, NPU3:-150.0ms
- Lifecycle cluster CI, per query class (C5): CI [464.2, 467.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=12, median=0.1543s
- Isolated: n=12, median=0.1551s
- Prefill saved (median): +0.8ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+0.7ms, NPU1:+1.4ms, NPU2:-2.1ms, NPU3:-0.8ms
- Lifecycle cluster CI, per query class (C5): CI [-1.3, 1.7]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=12, median=0.1031s
- Isolated: n=12, median=0.1590s
- Prefill saved (median): +55.9ms
- DMA cost (per-request, bound): 2.0ms
- Per-instance median paired delta (D5): NPU0:+52.4ms, NPU1:+59.4ms, NPU2:+47.7ms, NPU3:+65.3ms
- Lifecycle cluster CI, per query class (C5): CI [39.7, 47.2]ms excludes 0
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
- Median TTFT: 0.9450s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-083540
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
- Command: `python scripts/run_perf_t5-d_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 4`

