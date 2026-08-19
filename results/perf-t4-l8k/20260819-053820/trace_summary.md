# T4: prompt length 8k tokens Summary

## Environment
- Commit: `bcbef5696cf9` (parent: `c3de38816def`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T05:38:31+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1396** | 0.1796 | 0.1334 | [0.1545, 0.2090] | 0.1293 | 0.3143 |
| Isolated | 24 | **0.1387** | 0.2899 | 0.5204 | [0.2023, 0.3987] | 0.1292 | 0.6672 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.2262** | 1.2670 | 0.1440 | [1.2408, 1.2982] | 1.2108 | 1.4117 |
| Isolated | 24 | **1.2270** | 1.3769 | 0.5194 | [1.2890, 1.4856] | 1.2134 | 1.7602 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.2802s
- Isolated: n=8, median=0.6628s
- Prefill saved (median): +382.6ms
- DMA cost (per-request, bound): 59.6ms
- Per-instance median paired delta (D5): NPU0:+361.0ms, NPU1:-125.4ms, NPU2:+348.5ms, NPU3:+384.2ms, NPU4:+379.9ms, NPU5:+387.4ms, NPU6:+518.3ms, NPU7:+377.6ms
- Lifecycle cluster CI, per query class (C5): CI [328.9, 328.9]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=8, median=0.1391s
- Isolated: n=8, median=0.1381s
- Prefill saved (median): -1.0ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-5.0ms, NPU1:+0.5ms, NPU2:+4.4ms, NPU3:+5.4ms, NPU4:+6.2ms, NPU5:-1.0ms, NPU6:+0.7ms, NPU7:-3.1ms
- Lifecycle cluster CI, per query class (C5): CI [1.0, 1.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1347s
- Isolated: n=8, median=0.1374s
- Prefill saved (median): +2.7ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-8.2ms, NPU1:+4.1ms, NPU2:+1.1ms, NPU3:+8.2ms, NPU4:+5.3ms, NPU5:-0.7ms, NPU6:+0.2ms, NPU7:-2.9ms
- Lifecycle cluster CI, per query class (C5): CI [0.9, 0.9]ms excludes 0
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
- Median TTFT: 0.6619s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-053820
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
- Command: `python scripts/run_perf_t4-l8k_baseline.py --cycles 1 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

