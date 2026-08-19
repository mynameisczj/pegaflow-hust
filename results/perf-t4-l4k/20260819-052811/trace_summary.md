# T4: prompt length 4k tokens Summary

## Environment
- Commit: `bcbef5696cf9` (parent: `c3de38816def`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T05:28:21+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1243** | 0.1565 | 0.1077 | [0.1374, 0.1794] | 0.1180 | 0.2487 |
| Isolated | 24 | **0.1244** | 0.1837 | 0.2072 | [0.1487, 0.2270] | 0.1145 | 0.3400 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.1734** | 1.2059 | 0.1143 | [1.1856, 1.2301] | 1.1586 | 1.3064 |
| Isolated | 24 | **1.1717** | 1.2305 | 0.2140 | [1.1944, 1.2743] | 1.1589 | 1.3960 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.2362s
- Isolated: n=8, median=0.3312s
- Prefill saved (median): +95.0ms
- DMA cost (per-request, bound): 32.0ms
- Per-instance median paired delta (D5): NPU0:+203.7ms, NPU1:+95.0ms, NPU2:+95.3ms, NPU3:+103.8ms, NPU4:-109.0ms, NPU5:+82.4ms, NPU6:+109.1ms, NPU7:+90.6ms
- Lifecycle cluster CI, per query class (C5): CI [83.9, 83.9]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=8, median=0.1245s
- Isolated: n=8, median=0.1238s
- Prefill saved (median): -0.7ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-11.7ms, NPU1:-1.6ms, NPU2:-3.2ms, NPU3:+2.2ms, NPU4:-1.3ms, NPU5:-4.9ms, NPU6:+0.6ms, NPU7:+0.2ms
- Lifecycle cluster CI, per query class (C5): CI [-2.5, -2.5]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1223s
- Isolated: n=8, median=0.1244s
- Prefill saved (median): +2.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-3.8ms, NPU1:+0.1ms, NPU2:-6.6ms, NPU3:+0.9ms, NPU4:-2.0ms, NPU5:+1.0ms, NPU6:+7.6ms, NPU7:+5.3ms
- Lifecycle cluster CI, per query class (C5): CI [0.3, 0.3]ms excludes 0
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
- Count: 2
- Median TTFT: 0.3285s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-052811
- Total records: 50
- Consumer shared records: 24
- Consumer isolated records: 24
- Producer records: 2
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: PASS
- Audit verdict: VALID

## Reproduce
- Command: `python scripts/run_perf_t4-l4k_baseline.py --cycles 1 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

