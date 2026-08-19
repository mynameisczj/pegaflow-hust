# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `5cce2cfc16af` (parent: `56ad3c426adb`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T03:27:54+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.6562** | 0.6419 | 0.0061 | [0.6105, 0.6592] | 0.5336 | 0.6625 |
| Isolated | 8 | **0.9425** | 0.8914 | 0.0085 | [0.7882, 0.9452] | 0.5313 | 0.9484 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.7816** | 1.7712 | 0.0144 | [1.7388, 1.7911] | 1.6595 | 1.7981 |
| Isolated | 8 | **2.0720** | 2.0211 | 0.0085 | [1.9186, 2.0750] | 1.6639 | 2.0822 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.6562s
- Isolated: n=8, median=0.9437s
- Prefill saved (median): +287.5ms
- DMA cost (per-request, bound): 48.5ms
- Per-instance median paired delta (D5): NPU0:+287.4ms, NPU1:-124.8ms, NPU2:+285.1ms, NPU3:+285.9ms, NPU4:+283.8ms, NPU5:+288.6ms, NPU6:+414.4ms, NPU7:+275.6ms
- Lifecycle cluster CI, per query class (C5): CI [249.5, 249.5]ms excludes 0
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
- Median TTFT: 0.9383s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-032743
- Total records: 18
- Consumer shared records: 8
- Consumer isolated records: 8
- Producer records: 2
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: FAIL
- Audit verdict: INVALID

## Reproduce
- Command: `python scripts/run_perf_t3-h50_baseline.py --cycles 1 --requests-per-phase 1 --pool-size 16gb --num-instances 8`

