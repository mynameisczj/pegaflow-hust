# T3: hit rate 100% (prefix manipulation) Summary

## Environment
- Commit: `63431be6eadf` (parent: `5cce2cfc16af`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T04:06:21+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.3241** | 0.3075 | 0.0244 | [0.2638, 0.3345] | 0.1593 | 0.3435 |
| Isolated | 8 | **0.9350** | 0.8394 | 0.0105 | [0.6420, 0.9416] | 0.1503 | 0.9513 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.4521** | 1.4369 | 0.0217 | [1.3965, 1.4627] | 1.2992 | 1.4752 |
| Isolated | 8 | **2.0629** | 1.9683 | 0.0158 | [1.7696, 2.0727] | 1.2764 | 2.0863 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.3269s
- Isolated: n=8, median=0.9358s
- Prefill saved (median): +608.9ms
- DMA cost (per-request, bound): 95.6ms
- Per-instance median paired delta (D5): NPU0:+614.1ms, NPU1:-9.0ms, NPU2:+614.5ms, NPU3:+609.5ms, NPU4:+617.8ms, NPU5:+599.6ms, NPU6:+607.3ms, NPU7:+602.0ms
- Lifecycle cluster CI, per query class (C5): CI [532.0, 532.0]ms excludes 0
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
- Median TTFT: 0.9340s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-040610
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
- Command: `python scripts/run_perf_t3-h100_baseline.py --cycles 1 --requests-per-phase 1 --pool-size 16gb --num-instances 8`

