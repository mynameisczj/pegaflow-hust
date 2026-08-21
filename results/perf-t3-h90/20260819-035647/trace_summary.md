# T3: hit rate 90% (prefix manipulation) Summary

## Environment
- Commit: `63431be6eadf` (parent: `5cce2cfc16af`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T03:56:58+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.3413** | 0.3205 | 0.0169 | [0.2799, 0.3454] | 0.1806 | 0.3531 |
| Isolated | 8 | **0.9355** | 0.8451 | 0.0159 | [0.6549, 0.9445] | 0.1839 | 0.9553 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.4703** | 1.4515 | 0.0252 | [1.4088, 1.4800] | 1.3073 | 1.4997 |
| Isolated | 8 | **2.0649** | 1.9720 | 0.0181 | [1.7801, 2.0741] | 1.3046 | 2.0908 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.3428s
- Isolated: n=8, median=0.9381s
- Prefill saved (median): +595.3ms
- DMA cost (per-request, bound): 80.3ms
- Per-instance median paired delta (D5): NPU0:+588.3ms, NPU1:-169.2ms, NPU2:+615.8ms, NPU3:+760.7ms, NPU4:+605.5ms, NPU5:+594.5ms, NPU6:+590.1ms, NPU7:+611.3ms
- Lifecycle cluster CI, per query class (C5): CI [524.6, 524.6]ms excludes 0
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
- Median TTFT: 0.9375s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-035647
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
- Command: `python scripts/run_perf_t3-h90_baseline.py --cycles 1 --requests-per-phase 1 --pool-size 16gb --num-instances 8`

