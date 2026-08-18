# T1: Baseline Matched Evaluation (Qwen3-8B, 8 instances) Summary

## Environment
- Commit: `40e464db5989` (parent: `56be7867a81d`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T07:21:40+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1499** | 0.1929 | 0.2404 | [0.1694, 0.2176] | 0.0935 | 0.3783 |
| Isolated | 72 | **0.1553** | 0.3814 | 0.7827 | [0.3045, 0.4693] | 0.1423 | 0.9491 |

## TBT p50 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0179** | 0.0179 | 0.0001 | [0.0179, 0.0179] | 0.0177 | 0.0181 |
| Isolated | 72 | **0.0179** | 0.0179 | 0.0002 | [0.0179, 0.0179] | 0.0177 | 0.0181 |

## TBT p95 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0188** | 0.0189 | 0.0003 | [0.0188, 0.0190] | 0.0185 | 0.0211 |
| Isolated | 72 | **0.0187** | 0.0189 | 0.0003 | [0.0188, 0.0190] | 0.0185 | 0.0207 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2639** | 1.3069 | 0.2363 | [1.2830, 1.3322] | 1.1986 | 1.4942 |
| Isolated | 72 | **1.2679** | 1.4948 | 0.7844 | [1.4171, 1.5835] | 1.2504 | 2.0662 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3491s
- Isolated: n=24, median=0.9368s
- Prefill saved (median): +587.7ms
- DMA cost (per-request, bound): 114.3ms
- Per-instance median paired delta (D5): NPU0:+585.1ms, NPU1:-189.4ms, NPU2:+608.5ms, NPU3:+781.8ms, NPU4:+597.9ms, NPU5:+573.1ms, NPU6:+585.4ms, NPU7:+578.3ms
- Lifecycle cluster CI, per query class (C5): CI [507.2, 519.3]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1496s
- Isolated: n=24, median=0.1500s
- Prefill saved (median): +0.4ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-3.3ms, NPU1:-1.3ms, NPU2:-3.7ms, NPU3:+4.4ms, NPU4:+0.1ms, NPU5:+7.0ms, NPU6:-0.4ms, NPU7:+1.9ms
- Lifecycle cluster CI, per query class (C5): CI [-0.4, 2.1]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0968s
- Isolated: n=24, median=0.1552s
- Prefill saved (median): +58.4ms
- DMA cost (per-request, bound): 2.7ms
- Per-instance median paired delta (D5): NPU0:+55.3ms, NPU1:+58.7ms, NPU2:+51.6ms, NPU3:+8.7ms, NPU4:+58.0ms, NPU5:+61.3ms, NPU6:+58.7ms, NPU7:+59.8ms
- Lifecycle cluster CI, per query class (C5): CI [50.5, 52.3]ms excludes 0
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
- Median TTFT: 0.9366s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] leftover DMA completions: 258 unbound to any prefetch

## Validity Manifest
- Run ID: 20260818-072129
- Total records: 150
- Consumer shared records: 72
- Consumer isolated records: 72
- Producer records: 6
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: BROKEN (connector dup=0, orphans=0/0/0, leftover DMA=258, fallback-only DMA=0)
- Validity gate: FAIL
- Audit verdict: INVALID

## Reproduce
- Command: `python scripts/run_perf_t1_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

