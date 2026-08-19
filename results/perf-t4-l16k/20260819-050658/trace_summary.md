# T4: prompt length 16k tokens Summary

## Environment
- Commit: `c3de38816def` (parent: `63431be6eadf`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T05:07:08+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1113** | 0.1298 | 0.0651 | [0.1179, 0.1440] | 0.1039 | 0.1889 |
| Isolated | 24 | **0.1122** | 0.1289 | 0.0665 | [0.1174, 0.1426] | 0.1015 | 0.1825 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.0991** | 1.1181 | 0.0707 | [1.1045, 1.1338] | 1.0839 | 1.1851 |
| Isolated | 24 | **1.0985** | 1.1165 | 0.0692 | [1.1041, 1.1317] | 1.0820 | 1.1792 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.1809s
- Isolated: n=8, median=0.1768s
- Prefill saved (median): -4.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-2.7ms, NPU1:-7.0ms, NPU2:+4.2ms, NPU3:+4.3ms, NPU4:-3.5ms, NPU5:+0.7ms, NPU6:-4.1ms, NPU7:-3.6ms
- Lifecycle cluster CI, per query class (C5): CI [-1.5, -1.5]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q1
- Shared: n=8, median=0.1099s
- Isolated: n=8, median=0.1106s
- Prefill saved (median): +0.7ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+0.7ms, NPU1:-0.5ms, NPU2:-2.5ms, NPU3:+0.7ms, NPU4:+5.8ms, NPU5:-0.8ms, NPU6:-5.4ms, NPU7:+4.8ms
- Lifecycle cluster CI, per query class (C5): CI [0.4, 0.4]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1129s
- Isolated: n=8, median=0.1103s
- Prefill saved (median): -2.6ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-0.9ms, NPU1:-3.3ms, NPU2:-2.4ms, NPU3:-1.0ms, NPU4:-3.0ms, NPU5:-1.2ms, NPU6:-2.2ms, NPU7:+0.0ms
- Lifecycle cluster CI, per query class (C5): CI [-1.8, -1.8]ms excludes 0
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
- Median TTFT: 0.1779s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-050658
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
- Command: `python scripts/run_perf_t4-l16k_baseline.py --cycles 1 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

