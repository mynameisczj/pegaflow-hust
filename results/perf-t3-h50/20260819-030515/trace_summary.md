# T3: hit rate 50% (prefix manipulation) Summary

## Environment
- Commit: `c3582fcbb855` (parent: `5b992ea07376`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T03:05:27+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **0.6539** | 0.6407 | 0.0073 | [0.6093, 0.6591] | 0.5327 | 0.6654 |
| Isolated | 8 | **0.9448** | 0.8925 | 0.0118 | [0.7889, 0.9475] | 0.5309 | 0.9516 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 8 | **1.7840** | 1.7686 | 0.0075 | [1.7366, 1.7869] | 1.6574 | 1.7903 |
| Isolated | 8 | **2.0729** | 2.0205 | 0.0113 | [1.9149, 2.0770] | 1.6515 | 2.0821 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.6548s
- Isolated: n=8, median=0.9451s
- Prefill saved (median): +290.3ms
- DMA cost (per-request, bound): 46.2ms
- Per-instance median paired delta (D5): NPU0:-116.7ms, NPU1:+285.1ms, NPU2:+297.3ms, NPU3:+293.5ms, NPU4:+291.8ms, NPU5:+411.9ms, NPU6:+285.2ms, NPU7:+266.3ms
- Lifecycle cluster CI, per query class (C5): CI [251.8, 251.8]ms excludes 0
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
- Median TTFT: 0.9371s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] T3 gate FAILED: measured hit rate 43.2% vs target 50% (deviation > 5pp)

## Validity Manifest
- Run ID: 20260819-030515
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

