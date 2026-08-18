# T1: Baseline Matched Evaluation (Qwen3-8B, 8 instances) Summary

## Environment
- Commit: `f76003dace00` (parent: `686917b3d8bb`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T10:46:29+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1502** | 0.1867 | 0.2173 | [0.1653, 0.2086] | 0.0936 | 0.3422 |
| Isolated | 72 | **0.1573** | 0.3824 | 0.7793 | [0.3055, 0.4701] | 0.1411 | 0.9478 |

## TBT p50 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0181** | 0.0181 | 0.0002 | [0.0181, 0.0181] | 0.0179 | 0.0183 |
| Isolated | 72 | **0.0181** | 0.0181 | 0.0002 | [0.0181, 0.0181] | 0.0178 | 0.0183 |

## TBT p95 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0189** | 0.0190 | 0.0003 | [0.0189, 0.0191] | 0.0186 | 0.0205 |
| Isolated | 72 | **0.0189** | 0.0190 | 0.0002 | [0.0189, 0.0190] | 0.0186 | 0.0201 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2738** | 1.3116 | 0.2165 | [1.2899, 1.3340] | 1.2106 | 1.4713 |
| Isolated | 72 | **1.2810** | 1.5070 | 0.7834 | [1.4292, 1.5958] | 1.2520 | 2.0883 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3283s
- Isolated: n=24, median=0.9374s
- Prefill saved (median): +609.1ms
- DMA cost (per-request, bound): 90.5ms
- Per-instance median paired delta (D5): NPU0:+603.2ms, NPU1:+608.1ms, NPU2:+602.3ms, NPU3:+628.4ms, NPU4:+624.5ms, NPU5:+604.5ms, NPU6:+608.7ms, NPU7:+600.6ms
- Lifecycle cluster CI, per query class (C5): CI [531.6, 535.5]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1499s
- Isolated: n=24, median=0.1512s
- Prefill saved (median): +1.3ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-8.9ms, NPU1:+1.4ms, NPU2:-5.0ms, NPU3:+1.9ms, NPU4:+4.8ms, NPU5:-0.6ms, NPU6:+3.0ms, NPU7:+4.4ms
- Lifecycle cluster CI, per query class (C5): CI [-0.2, 3.1]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0970s
- Isolated: n=24, median=0.1579s
- Prefill saved (median): +60.9ms
- DMA cost (per-request, bound): 2.0ms
- Per-instance median paired delta (D5): NPU0:+53.7ms, NPU1:+61.3ms, NPU2:+55.1ms, NPU3:+64.5ms, NPU4:+59.8ms, NPU5:+55.6ms, NPU6:+61.8ms, NPU7:+58.1ms
- Lifecycle cluster CI, per query class (C5): CI [51.3, 51.9]ms excludes 0
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
- Median TTFT: 0.9384s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-104618
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
- Command: `python scripts/run_perf_t1_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

