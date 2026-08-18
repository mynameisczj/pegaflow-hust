# T2: concurrency=8 interval=0ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T15:31:36+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1595** | 0.2241 | 0.2278 | [0.2002, 0.2505] | 0.1408 | 0.4122 |
| Isolated | 72 | **0.1599** | 0.3868 | 0.7851 | [0.3096, 0.4750] | 0.1439 | 0.9563 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2855** | 1.3504 | 0.2304 | [1.3260, 1.3773] | 1.2595 | 1.5449 |
| Isolated | 72 | **1.2868** | 1.5123 | 0.7867 | [1.4345, 1.6011] | 1.2610 | 2.0863 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3843s
- Isolated: n=24, median=0.9430s
- Prefill saved (median): +558.7ms
- DMA cost (per-request, bound): 145.0ms
- Per-instance median paired delta (D5): NPU0:+535.6ms, NPU1:+555.9ms, NPU2:+579.0ms, NPU3:+564.7ms, NPU4:+564.9ms, NPU5:+569.9ms, NPU6:+555.3ms, NPU7:+579.2ms
- Lifecycle cluster CI, per query class (C5): CI [477.9, 491.9]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1518s
- Isolated: n=24, median=0.1540s
- Prefill saved (median): +2.2ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+3.6ms, NPU1:+4.7ms, NPU2:-1.0ms, NPU3:+2.2ms, NPU4:+3.5ms, NPU5:-0.1ms, NPU6:+9.9ms, NPU7:+0.2ms
- Lifecycle cluster CI, per query class (C5): CI [1.9, 5.1]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.1596s
- Isolated: n=24, median=0.1603s
- Prefill saved (median): +0.7ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-4.5ms, NPU1:+4.7ms, NPU2:-3.5ms, NPU3:+0.7ms, NPU4:+5.5ms, NPU5:-2.0ms, NPU6:+8.4ms, NPU7:-2.1ms
- Lifecycle cluster CI, per query class (C5): CI [-1.4, 4.8]ms includes 0
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
- Median TTFT: 0.9360s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-153124
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
- Command: `python scripts/run_perf_t2-c8-i0_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

