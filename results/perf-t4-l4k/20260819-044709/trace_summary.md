# T4: prompt length 4k tokens Summary

## Environment
- Commit: `c3de38816def` (parent: `63431be6eadf`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T04:47:20+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1100** | 0.1281 | 0.0648 | [0.1163, 0.1422] | 0.0983 | 0.1872 |
| Isolated | 24 | **0.1113** | 0.1299 | 0.0668 | [0.1186, 0.1436] | 0.1046 | 0.1822 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.0983** | 1.1157 | 0.0765 | [1.1019, 1.1317] | 1.0756 | 1.1876 |
| Isolated | 24 | **1.0952** | 1.1167 | 0.0716 | [1.1044, 1.1314] | 1.0891 | 1.1738 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.1793s
- Isolated: n=8, median=0.1768s
- Prefill saved (median): -2.5ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-63.3ms, NPU1:-2.4ms, NPU2:+16.8ms, NPU3:-6.9ms, NPU4:+70.2ms, NPU5:+2.1ms, NPU6:-10.5ms, NPU7:-2.2ms
- Lifecycle cluster CI, per query class (C5): CI [0.5, 0.5]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q1
- Shared: n=8, median=0.1092s
- Isolated: n=8, median=0.1100s
- Prefill saved (median): +0.8ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+10.3ms, NPU1:+8.0ms, NPU2:+9.6ms, NPU3:+0.2ms, NPU4:-1.5ms, NPU5:-6.2ms, NPU6:-4.3ms, NPU7:+5.9ms
- Lifecycle cluster CI, per query class (C5): CI [2.8, 2.8]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1086s
- Isolated: n=8, median=0.1104s
- Prefill saved (median): +1.8ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+13.0ms, NPU1:+1.3ms, NPU2:+10.6ms, NPU3:+2.0ms, NPU4:+1.4ms, NPU5:-1.4ms, NPU6:-4.5ms, NPU7:-5.5ms
- Lifecycle cluster CI, per query class (C5): CI [2.1, 2.1]ms excludes 0
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
- Median TTFT: 0.1774s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-044709
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

