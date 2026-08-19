# T5 combo b: gmu=0.85 external=True Summary

## Environment
- Commit: `7c4b7323f0d1` (parent: `54e132aeb68a`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T08:10:19+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **0.1515** | 0.1840 | 0.1749 | [0.1561, 0.2160] | 0.0964 | 0.3515 |
| Isolated | 36 | **0.1568** | 0.3493 | 0.7790 | [0.2404, 0.4591] | 0.1435 | 0.9429 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 36 | **1.2792** | 1.3092 | 0.1773 | [1.2793, 1.3425] | 1.2103 | 1.4839 |
| Isolated | 36 | **1.2806** | 1.4719 | 0.7883 | [1.3624, 1.5833] | 1.2592 | 2.0709 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=12, median=0.3309s
- Isolated: n=12, median=0.9342s
- Prefill saved (median): +603.3ms
- DMA cost (per-request, bound): 99.4ms
- Per-instance median paired delta (D5): NPU0:+605.2ms, NPU1:+585.0ms, NPU2:+625.0ms, NPU3:+587.5ms
- Lifecycle cluster CI, per query class (C5): CI [446.1, 460.5]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=12, median=0.1524s
- Isolated: n=12, median=0.1525s
- Prefill saved (median): +0.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+3.6ms, NPU1:+0.7ms, NPU2:+0.9ms, NPU3:-3.2ms
- Lifecycle cluster CI, per query class (C5): CI [-1.1, 3.9]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=12, median=0.1004s
- Isolated: n=12, median=0.1564s
- Prefill saved (median): +56.0ms
- DMA cost (per-request, bound): 2.0ms
- Per-instance median paired delta (D5): NPU0:+48.8ms, NPU1:+8.5ms, NPU2:+54.5ms, NPU3:+62.1ms
- Lifecycle cluster CI, per query class (C5): CI [40.9, 45.3]ms excludes 0
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
- Median TTFT: 0.9401s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-081008
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
- Command: `python scripts/run_perf_t5-b_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 4`

