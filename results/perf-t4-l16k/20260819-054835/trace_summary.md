# T4: prompt length 16k tokens Summary

## Environment
- Commit: `bcbef5696cf9` (parent: `c3de38816def`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-19T05:48:46+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1654** | 0.2194 | 0.1769 | [0.1866, 0.2593] | 0.1538 | 0.3739 |
| Isolated | 24 | **0.1652** | 0.4910 | 1.1180 | [0.3023, 0.7259] | 0.1525 | 1.3052 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.3119** | 1.3645 | 0.1827 | [1.3306, 1.4053] | 1.2909 | 1.5301 |
| Isolated | 24 | **1.3064** | 1.6331 | 1.1277 | [1.4433, 1.8689] | 1.2854 | 2.4568 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.3637s
- Isolated: n=8, median=1.2936s
- Prefill saved (median): +929.9ms
- DMA cost (per-request, bound): 108.9ms
- Per-instance median paired delta (D5): NPU0:-182.5ms, NPU1:+1120.3ms, NPU2:+921.6ms, NPU3:+960.5ms, NPU4:+941.5ms, NPU5:+918.7ms, NPU6:+919.7ms, NPU7:+926.9ms
- Lifecycle cluster CI, per query class (C5): CI [815.8, 815.8]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=8, median=0.1652s
- Isolated: n=8, median=0.1633s
- Prefill saved (median): -1.9ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-5.3ms, NPU1:-5.8ms, NPU2:+0.8ms, NPU3:-4.2ms, NPU4:-2.1ms, NPU5:+0.8ms, NPU6:+3.1ms, NPU7:+4.0ms
- Lifecycle cluster CI, per query class (C5): CI [-1.1, -1.1]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1629s
- Isolated: n=8, median=0.1640s
- Prefill saved (median): +1.1ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-2.4ms, NPU1:+1.6ms, NPU2:-0.7ms, NPU3:-4.1ms, NPU4:-0.5ms, NPU5:-1.3ms, NPU6:+5.8ms, NPU7:+1.1ms
- Lifecycle cluster CI, per query class (C5): CI [-0.1, -0.1]ms excludes 0
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
- Median TTFT: 1.2782s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260819-054835
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

