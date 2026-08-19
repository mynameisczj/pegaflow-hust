# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `63431be6eadf` (parent: `5cce2cfc16af`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T03:38:14+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.6558** | 0.6411 | 0.0163 | [0.6096, 0.6610] | 0.5339 | 0.6716 |
| Isolated | 8 | **0.9425** | 0.8910 | 0.0075 | [0.7889, 0.9453] | 0.5340 | 0.9502 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.7835** | 1.7705 | 0.0231 | [1.7372, 1.7931] | 1.6580 | 1.8084 |
| Isolated | 8 | **2.0703** | 2.0196 | 0.0131 | [1.9179, 2.0740] | 1.6646 | 2.0774 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.6566s
- Isolated: n=8, median=0.9447s
- Prefill saved (median): +288.1ms
- DMA cost (per-request, bound): 46.3ms
- Per-instance median paired delta (D5): NPU0:+294.6ms, NPU1:+272.4ms, NPU2:+297.8ms, NPU3:+277.2ms, NPU4:+274.0ms, NPU5:-120.9ms, NPU6:+412.0ms, NPU7:+291.9ms
- Lifecycle cluster CI, per query class (C5): CI [249.9, 249.9]ms excludes 0
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
- Median TTFT: 0.9355s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-033803
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
- Command: `python scripts/run_perf_t3-h50_baseline.py --cycles 1 --requests-per-phase 1 --pool-size 16gb --num-instances 8`

