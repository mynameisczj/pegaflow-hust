# T2: concurrency=1 interval=0ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T11:19:16+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1493** | 0.1876 | 0.2231 | [0.1659, 0.2098] | 0.0947 | 0.3449 |
| Isolated | 72 | **0.1563** | 0.3826 | 0.7817 | [0.3059, 0.4703] | 0.1430 | 0.9526 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2738** | 1.3126 | 0.2223 | [1.2902, 1.3356] | 1.2111 | 1.4771 |
| Isolated | 72 | **1.2822** | 1.5063 | 0.7838 | [1.4287, 1.5948] | 1.2586 | 2.0814 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3319s
- Isolated: n=24, median=0.9375s
- Prefill saved (median): +605.6ms
- DMA cost (per-request, bound): 94.8ms
- Per-instance median paired delta (D5): NPU0:+618.0ms, NPU1:-183.8ms, NPU2:+610.9ms, NPU3:+601.9ms, NPU4:+618.9ms, NPU5:+614.9ms, NPU6:+608.0ms, NPU7:+595.2ms
- Lifecycle cluster CI, per query class (C5): CI [528.6, 533.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1492s
- Isolated: n=24, median=0.1521s
- Prefill saved (median): +2.9ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-0.3ms, NPU1:-0.2ms, NPU2:+2.3ms, NPU3:+3.2ms, NPU4:-1.3ms, NPU5:+3.2ms, NPU6:-5.3ms, NPU7:-2.5ms
- Lifecycle cluster CI, per query class (C5): CI [-1.0, 3.0]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0970s
- Isolated: n=24, median=0.1565s
- Prefill saved (median): +59.5ms
- DMA cost (per-request, bound): 2.0ms
- Per-instance median paired delta (D5): NPU0:+53.6ms, NPU1:+61.5ms, NPU2:+58.4ms, NPU3:+59.2ms, NPU4:+61.2ms, NPU5:+63.2ms, NPU6:+56.7ms, NPU7:+60.0ms
- Lifecycle cluster CI, per query class (C5): CI [51.6, 54.5]ms excludes 0
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
- Median TTFT: 0.9355s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-111905
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
- Command: `python scripts/run_perf_t2-c1-i0_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

