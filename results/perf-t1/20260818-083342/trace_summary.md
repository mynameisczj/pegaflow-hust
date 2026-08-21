# T1: Baseline Matched Evaluation (Qwen3-8B, 8 instances) Summary

## Environment
- Commit: `40e464db5989` (parent: `56be7867a81d`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T08:33:53+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1507** | 0.1952 | 0.2444 | [0.1715, 0.2208] | 0.0945 | 0.3882 |
| Isolated | 72 | **0.1565** | 0.3816 | 0.7837 | [0.3047, 0.4694] | 0.1410 | 0.9455 |

## TBT p50 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0179** | 0.0179 | 0.0001 | [0.0179, 0.0179] | 0.0177 | 0.0181 |
| Isolated | 72 | **0.0179** | 0.0179 | 0.0001 | [0.0179, 0.0179] | 0.0177 | 0.0182 |

## TBT p95 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0188** | 0.0188 | 0.0002 | [0.0188, 0.0189] | 0.0186 | 0.0210 |
| Isolated | 72 | **0.0188** | 0.0188 | 0.0003 | [0.0187, 0.0189] | 0.0185 | 0.0200 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2668** | 1.3097 | 0.2442 | [1.2858, 1.3360] | 1.1983 | 1.5086 |
| Isolated | 72 | **1.2706** | 1.4947 | 0.7851 | [1.4168, 1.5834] | 1.2448 | 2.0686 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3577s
- Isolated: n=24, median=0.9386s
- Prefill saved (median): +580.9ms
- DMA cost (per-request, bound): 120.2ms
- Per-instance median paired delta (D5): NPU0:+583.1ms, NPU1:+602.3ms, NPU2:+571.7ms, NPU3:+607.5ms, NPU4:+594.0ms, NPU5:+575.3ms, NPU6:+572.0ms, NPU7:+575.5ms
- Lifecycle cluster CI, per query class (C5): CI [503.5, 512.4]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1504s
- Isolated: n=24, median=0.1512s
- Prefill saved (median): +0.8ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+0.4ms, NPU1:+3.3ms, NPU2:-4.3ms, NPU3:-2.3ms, NPU4:+3.3ms, NPU5:-0.4ms, NPU6:+1.8ms, NPU7:+0.3ms
- Lifecycle cluster CI, per query class (C5): CI [-2.5, 2.0]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0979s
- Isolated: n=24, median=0.1566s
- Prefill saved (median): +58.7ms
- DMA cost (per-request, bound): 3.5ms
- Per-instance median paired delta (D5): NPU0:+54.5ms, NPU1:+60.6ms, NPU2:+52.5ms, NPU3:+60.8ms, NPU4:+56.9ms, NPU5:+53.9ms, NPU6:+61.4ms, NPU7:+62.8ms
- Lifecycle cluster CI, per query class (C5): CI [48.3, 51.5]ms excludes 0
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
- Median TTFT: 0.9400s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] leftover DMA completions: 258 unbound to any prefetch

## Validity Manifest
- Run ID: 20260818-083342
- Total records: 150
- Consumer shared records: 72
- Consumer isolated records: 72
- Producer records: 6
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: BROKEN (connector dup=0, orphans=0/0/0, leftover DMA=258, fallback DMA (bound)=0)
- Validity gate: FAIL
- Audit verdict: INVALID

## Reproduce
- Command: `python scripts/run_perf_t1_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

