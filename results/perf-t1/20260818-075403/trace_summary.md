# T1: Baseline Matched Evaluation (Qwen3-8B, 8 instances) Summary

## Environment
- Commit: `40e464db5989` (parent: `56be7867a81d`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T07:54:14+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.1504** | 0.1938 | 0.2386 | [0.1708, 0.2190] | 0.0926 | 0.3796 |
| Isolated | 72 | **0.1537** | 0.3812 | 0.7788 | [0.3044, 0.4691] | 0.1394 | 0.9492 |

## TBT p50 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0179** | 0.0179 | 0.0001 | [0.0179, 0.0179] | 0.0177 | 0.0181 |
| Isolated | 72 | **0.0179** | 0.0179 | 0.0002 | [0.0179, 0.0179] | 0.0178 | 0.0183 |

## TBT p95 (decode, per-token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **0.0188** | 0.0188 | 0.0002 | [0.0188, 0.0189] | 0.0185 | 0.0203 |
| Isolated | 72 | **0.0187** | 0.0189 | 0.0003 | [0.0188, 0.0190] | 0.0185 | 0.0207 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 72 | **1.2633** | 1.3075 | 0.2384 | [1.2838, 1.3332] | 1.1998 | 1.5000 |
| Isolated | 72 | **1.2678** | 1.4954 | 0.7870 | [1.4176, 1.5844] | 1.2498 | 2.0863 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=24, median=0.3558s
- Isolated: n=24, median=0.9354s
- Prefill saved (median): +579.6ms
- DMA cost (per-request, bound): 117.3ms
- Per-instance median paired delta (D5): NPU0:+585.5ms, NPU1:+776.9ms, NPU2:+598.3ms, NPU3:+615.3ms, NPU4:+585.3ms, NPU5:+564.3ms, NPU6:+576.0ms, NPU7:+569.9ms
- Lifecycle cluster CI, per query class (C5): CI [510.5, 514.6]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=24, median=0.1494s
- Isolated: n=24, median=0.1504s
- Prefill saved (median): +1.0ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-2.1ms, NPU1:+2.2ms, NPU2:-8.4ms, NPU3:+3.3ms, NPU4:+1.5ms, NPU5:+1.8ms, NPU6:+0.9ms, NPU7:+3.6ms
- Lifecycle cluster CI, per query class (C5): CI [-1.1, 2.3]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=24, median=0.0988s
- Isolated: n=24, median=0.1534s
- Prefill saved (median): +54.6ms
- DMA cost (per-request, bound): 3.7ms
- Per-instance median paired delta (D5): NPU0:+52.2ms, NPU1:+13.2ms, NPU2:+52.5ms, NPU3:+56.0ms, NPU4:+56.7ms, NPU5:+55.3ms, NPU6:+62.3ms, NPU7:+51.0ms
- Lifecycle cluster CI, per query class (C5): CI [47.8, 51.9]ms excludes 0
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
- Median TTFT: 0.9364s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] leftover DMA completions: 258 unbound to any prefetch

## Validity Manifest
- Run ID: 20260818-075403
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

