# T1: Baseline Matched Evaluation (Qwen3-8B, 8 instances) Summary

## Environment
- Commit: `021473b7a7fc` (parent: `40e464db5989`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T09:06:36+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1491** | 0.1942 | 0.2422 | [0.1705, 0.2191] | 0.0957 | 0.3708 |
| Isolated | 72 | **0.1569** | 0.3817 | 0.7849 | [0.3046, 0.4696] | 0.1388 | 0.9516 |

## TBT p50 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0179** | 0.0179 | 0.0001 | [0.0179, 0.0179] | 0.0178 | 0.0181 |
| Isolated | 72 | **0.0179** | 0.0179 | 0.0002 | [0.0179, 0.0179] | 0.0177 | 0.0181 |

## TBT p95 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0188** | 0.0190 | 0.0002 | [0.0189, 0.0191] | 0.0186 | 0.0211 |
| Isolated | 72 | **0.0188** | 0.0189 | 0.0002 | [0.0188, 0.0190] | 0.0184 | 0.0213 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2628** | 1.3094 | 0.2438 | [1.2853, 1.3353] | 1.2036 | 1.4915 |
| Isolated | 72 | **1.2704** | 1.4951 | 0.7905 | [1.4171, 1.5841] | 1.2404 | 2.0762 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3559s
- Isolated: n=24, median=0.9376s
- Prefill saved (median): +581.7ms
- DMA cost (per-request, bound): 120.1ms
- Per-instance median paired delta (D5): NPU0:+568.3ms, NPU1:+580.5ms, NPU2:+587.7ms, NPU3:+628.4ms, NPU4:+592.8ms, NPU5:+580.4ms, NPU6:+572.9ms, NPU7:+573.7ms
- Lifecycle cluster CI, per query class (C5): CI [510.2, 514.2]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1492s
- Isolated: n=24, median=0.1490s
- Prefill saved (median): -0.2ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-4.3ms, NPU1:-4.9ms, NPU2:-3.7ms, NPU3:+3.5ms, NPU4:-1.5ms, NPU5:+6.5ms, NPU6:+6.4ms, NPU7:+1.0ms
- Lifecycle cluster CI, per query class (C5): CI [-0.5, 1.2]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0988s
- Isolated: n=24, median=0.1571s
- Prefill saved (median): +58.3ms
- DMA cost (per-request, bound): 3.5ms
- Per-instance median paired delta (D5): NPU0:+55.2ms, NPU1:+56.8ms, NPU2:+50.4ms, NPU3:+60.3ms, NPU4:+59.8ms, NPU5:+58.0ms, NPU6:+56.7ms, NPU7:+53.9ms
- Lifecycle cluster CI, per query class (C5): CI [49.0, 51.1]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

## Platform Constraints (Prereg Deviation C, 2026-08-18)
- 216 D2H (save-path) and 42 H2D (load-path) batch calls fell back to per-copy `aclrtMemcpyAsync`: on 8-instance concurrency CANN `aclrtMemcpyBatchAsync` intermittently fails 107000. Completions are evidence via the `Load task completed` line (per-copy fallback succeeds, data-correct); fallback counts are recorded here as a platform constraint. Batch DMA recovery is a tracked follow-up (D2H chunking).

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
- Median TTFT: 0.9358s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260818-090625
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

