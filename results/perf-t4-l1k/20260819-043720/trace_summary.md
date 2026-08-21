# T4: prompt length 1k tokens Summary

## Environment
- Commit: `c3de38816def` (parent: `63431be6eadf`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T04:37:30+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1139** | 0.1301 | 0.0651 | [0.1190, 0.1435] | 0.1049 | 0.1835 |
| Isolated | 24 | **0.1117** | 0.1294 | 0.0677 | [0.1181, 0.1430] | 0.1035 | 0.1805 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.1004** | 1.1185 | 0.0679 | [1.1062, 1.1334] | 1.0847 | 1.1784 |
| Isolated | 24 | **1.0964** | 1.1148 | 0.0696 | [1.1024, 1.1298] | 1.0801 | 1.1778 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.1772s
- Isolated: n=8, median=0.1771s
- Prefill saved (median): -0.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-2.3ms, NPU1:+59.7ms, NPU2:+5.7ms, NPU3:+2.9ms, NPU4:-1.0ms, NPU5:+5.7ms, NPU6:-8.1ms, NPU7:-61.2ms
- Lifecycle cluster CI, per query class (C5): CI [0.2, 0.2]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q1
- Shared: n=8, median=0.1135s
- Isolated: n=8, median=0.1094s
- Prefill saved (median): -4.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-0.2ms, NPU1:-4.1ms, NPU2:-2.3ms, NPU3:-6.4ms, NPU4:-8.5ms, NPU5:+11.5ms, NPU6:-11.5ms, NPU7:-0.9ms
- Lifecycle cluster CI, per query class (C5): CI [-2.8, -2.8]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1108s
- Isolated: n=8, median=0.1112s
- Prefill saved (median): +0.4ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+9.8ms, NPU1:+5.1ms, NPU2:-0.8ms, NPU3:+0.0ms, NPU4:-10.5ms, NPU5:+4.9ms, NPU6:-7.3ms, NPU7:+3.7ms
- Lifecycle cluster CI, per query class (C5): CI [0.6, 0.6]ms excludes 0
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
- Median TTFT: 0.1793s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-043720
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

