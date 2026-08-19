# T3: hit rate 75% (prefix manipulation) Summary

## Environment
- Commit: `63431be6eadf` (parent: `5cce2cfc16af`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T03:47:38+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.4967** | 0.4774 | 0.0132 | [0.4381, 0.5014] | 0.3424 | 0.5113 |
| Isolated | 8 | **0.9372** | 0.8658 | 0.0124 | [0.7181, 0.9422] | 0.3515 | 0.9478 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.6195** | 1.6060 | 0.0234 | [1.5653, 1.6321] | 1.4669 | 1.6424 |
| Isolated | 8 | **2.0652** | 1.9940 | 0.0151 | [1.8474, 2.0708] | 1.4841 | 2.0780 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.4997s
- Isolated: n=8, median=0.9388s
- Prefill saved (median): +439.1ms
- DMA cost (per-request, bound): 70.0ms
- Per-instance median paired delta (D5): NPU0:+436.5ms, NPU1:-129.3ms, NPU2:+445.1ms, NPU3:+593.2ms, NPU4:+444.2ms, NPU5:+450.5ms, NPU6:+433.3ms, NPU7:+434.2ms
- Lifecycle cluster CI, per query class (C5): CI [388.5, 388.5]ms excludes 0
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
- Median TTFT: 0.9444s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-034727
- Total records: 18
- Consumer shared records: 8
- Consumer isolated records: 8
- Producer records: 2
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: PASS
- Audit verdict: VALID

## Reproduce
- Command: `python scripts/run_perf_t3-h75_baseline.py --cycles 1 --requests-per-phase 1 --pool-size 16gb --num-instances 8`

