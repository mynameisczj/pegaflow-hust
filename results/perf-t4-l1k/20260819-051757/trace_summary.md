# T4: prompt length 1k tokens Summary

## Environment
- Commit: `bcbef5696cf9` (parent: `c3de38816def`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T05:18:08+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1161** | 0.1426 | 0.0962 | [0.1261, 0.1623] | 0.1090 | 0.2244 |
| Isolated | 24 | **0.1150** | 0.1353 | 0.0765 | [0.1218, 0.1512] | 0.1071 | 0.2038 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.1213** | 1.1491 | 0.1004 | [1.1314, 1.1700] | 1.1105 | 1.2391 |
| Isolated | 24 | **1.1201** | 1.1394 | 0.0851 | [1.1250, 1.1565] | 1.1026 | 1.2139 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.2122s
- Isolated: n=8, median=0.1910s
- Prefill saved (median): -21.2ms
- DMA cost (per-request, bound): 8.7ms
- Per-instance median paired delta (D5): NPU0:-33.4ms, NPU1:-26.1ms, NPU2:-24.8ms, NPU3:-16.5ms, NPU4:+77.7ms, NPU5:-14.0ms, NPU6:-8.4ms, NPU7:-90.8ms
- Lifecycle cluster CI, per query class (C5): CI [-17.0, -17.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q1
- Shared: n=8, median=0.1116s
- Isolated: n=8, median=0.1127s
- Prefill saved (median): +1.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-1.1ms, NPU1:-0.7ms, NPU2:-1.2ms, NPU3:-3.7ms, NPU4:+5.6ms, NPU5:-4.1ms, NPU6:+7.4ms, NPU7:-4.4ms
- Lifecycle cluster CI, per query class (C5): CI [-0.3, -0.3]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1159s
- Isolated: n=8, median=0.1112s
- Prefill saved (median): -4.7ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-11.4ms, NPU1:-1.0ms, NPU2:-5.2ms, NPU3:-9.0ms, NPU4:+1.8ms, NPU5:+2.3ms, NPU6:-5.8ms, NPU7:-8.3ms
- Lifecycle cluster CI, per query class (C5): CI [-4.6, -4.6]ms excludes 0
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
- Median TTFT: 0.1900s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-051757
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
- Command: `python scripts/run_perf_t4-l1k_baseline.py --cycles 1 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

