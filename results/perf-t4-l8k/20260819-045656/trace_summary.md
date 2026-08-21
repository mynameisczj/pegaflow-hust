# T4: prompt length 8k tokens Summary

## Environment
- Commit: `c3de38816def` (parent: `63431be6eadf`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T04:57:07+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1123** | 0.1309 | 0.0646 | [0.1189, 0.1451] | 0.1029 | 0.1978 |
| Isolated | 24 | **0.1094** | 0.1285 | 0.0672 | [0.1169, 0.1426] | 0.1025 | 0.1824 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.0982** | 1.1173 | 0.0739 | [1.1036, 1.1338] | 1.0829 | 1.1898 |
| Isolated | 24 | **1.0986** | 1.1170 | 0.0753 | [1.1047, 1.1319] | 1.0838 | 1.1730 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.1785s
- Isolated: n=8, median=0.1765s
- Prefill saved (median): -2.0ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+0.1ms, NPU1:-71.4ms, NPU2:+9.5ms, NPU3:-5.3ms, NPU4:-22.5ms, NPU5:+68.8ms, NPU6:-4.5ms, NPU7:+4.8ms
- Lifecycle cluster CI, per query class (C5): CI [-2.6, -2.6]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q1
- Shared: n=8, median=0.1116s
- Isolated: n=8, median=0.1072s
- Prefill saved (median): -4.4ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+2.7ms, NPU1:-4.6ms, NPU2:-0.1ms, NPU3:-3.1ms, NPU4:-15.7ms, NPU5:+4.8ms, NPU6:-9.3ms, NPU7:+0.1ms
- Lifecycle cluster CI, per query class (C5): CI [-3.2, -3.2]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1103s
- Isolated: n=8, median=0.1088s
- Prefill saved (median): -1.5ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:+5.5ms, NPU1:+0.7ms, NPU2:+0.4ms, NPU3:-2.1ms, NPU4:-9.5ms, NPU5:+0.4ms, NPU6:-4.0ms, NPU7:-1.7ms
- Lifecycle cluster CI, per query class (C5): CI [-1.3, -1.3]ms excludes 0
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
- Median TTFT: 0.1769s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-045656
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

