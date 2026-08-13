# Trace Audit Summary

## Environment
- Commit: `80521846ae8c` (parent: `c4c73583550c`)
- Branch: `feat/trace-audit-serving-boundary`
- Runtime vLLM commit: `4861aab3af39`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-13T09:08:23+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 45 | **0.2201s** | 0.2450s | 0.2088s | [0.2119, 0.2792] | 0.0945s | 0.4897s |
| Isolated | 45 | **0.2375s** | 0.4667s | 0.8556s | [0.3526, 0.5866] | 0.1544s | 1.2442s |

## Total Latency

| Phase | N | Median | Mean | IQR | 95% CI |
|---|---|---|---|---|---|
| Shared | 45 | 1.556s | 1.600s | 0.218s | [1.548, 1.654] |
| Isolated | 45 | 1.638s | 1.892s | 0.868s | [1.742, 2.057] |


## Per-Query Paired Analysis

Q0 measures cross-instance cold prefill (cache hit vs full compute).
Q1/Q2 measure same-instance prefix cache (vLLM internal).
Mixed-class mean conflates these — per-query pairing is the correct metric.

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)
### Q0
- Shared: n=15, median=0.3807s
- Isolated: n=15, median=1.0866s
- Prefill saved (median): +705.9ms
- DMA cost (per-request, bound): 88.7ms
- Per-instance median paired delta (D5): NPU3:+754.5ms, NPU4:+913.0ms, NPU5:+701.7ms, NPU6:+753.2ms, NPU7:+676.4ms
- Lifecycle cluster CI, per query class (C5): CI [546.4, 600.7]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**
### Q1
- Shared: n=15, median=0.2199s
- Isolated: n=15, median=0.2215s
- Prefill saved (median): +1.6ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU3:+121.2ms, NPU4:+25.2ms, NPU5:-51.3ms, NPU6:+16.6ms, NPU7:-18.1ms
- Lifecycle cluster CI, per query class (C5): CI [-57.1, 57.1]ms includes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**
### Q2
- Shared: n=15, median=0.1194s
- Isolated: n=15, median=0.1990s
- Prefill saved (median): +79.6ms
- DMA cost (per-request, bound): 3.0ms
- Per-instance median paired delta (D5): NPU3:+32.7ms, NPU4:+57.4ms, NPU5:+69.2ms, NPU6:+170.4ms, NPU7:+66.1ms
- Lifecycle cluster CI, per query class (C5): CI [22.5, 146.7]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

## Methodological Notes

- AB/BA arm order alternation per cycle (shared→isolated, isolated→shared, ...)
- Both arms use PegaFlow with symmetric warmup count
- Independent server lifecycle per arm (not shared across cycles)
- Per-query-class paired reporting (Q0 vs Q0, Q1 vs Q1, Q2 vs Q2)
- DMA cost per-request bound to corresponding hit (not shared mean)
- See prior artifact (results/trace-audit/) for methodological asymmetry discovered

## Per-Cycle TTFT (Lifecycle-Level Paired Delta)

Each lifecycle = 1 independent paired observation (shared - isolated).
Cluster bootstrap over n=3 lifecycles, per query class.

| Cycle | Shared Mean | Isolated Mean | Paired Delta |
|---|---|---|---|
| 1 | 0.2346s | 0.5028s | +0.2682s (+53.3%) |
| 2 | 0.2535s | 0.4348s | +0.1814s (+41.7%) |
| 3 | 0.2469s | 0.4624s | +0.2155s (+46.6%) |

## Lifecycle-Level Paired Delta (n=3 clusters)
- Mean paired delta: 222ms (shared saves 47.5% vs isolated mean)
- 95% CI (cluster bootstrap): [181ms, 268ms]
- Per-lifecycle deltas: C1:268ms, C2:181ms, C3:216ms

## Per-Query TTFT: Q-1

| Phase | N | Median | Mean | IQR | 95% CI |
|---|---|---|---|---|---|
| shared | 3 | **1.0560s** | 1.0666s | 0.0419s | [1.0509, 1.0928] |
| isolated | 3 | **1.0722s** | 1.0648s | 0.0347s | [1.0438, 1.0785] |

## Per-Query TTFT: Q0

| Phase | N | Median | Mean | IQR | 95% CI |
|---|---|---|---|---|---|
| shared | 15 | **0.3807s** | 0.3575s | 0.0394s | [0.3144, 0.3962] |
| isolated | 15 | **1.0866s** | 0.9328s | 0.0800s | [0.7430, 1.1116] |

## Per-Query TTFT: Q1

| Phase | N | Median | Mean | IQR | 95% CI |
|---|---|---|---|---|---|
| shared | 15 | **0.2199s** | 0.2379s | 0.0610s | [0.2093, 0.2689] |
| isolated | 15 | **0.2215s** | 0.2430s | 0.0486s | [0.2064, 0.2900] |

## Per-Query TTFT: Q2

| Phase | N | Median | Mean | IQR | 95% CI |
|---|---|---|---|---|---|
| shared | 15 | **0.1194s** | 0.1396s | 0.0367s | [0.1161, 0.1649] |
| isolated | 15 | **0.1990s** | 0.2242s | 0.0959s | [0.1969, 0.2544] |

## Negative Examples (Preserved)

### Burst Concurrent (PCIe DMA Contention)

- Shared avg TTFT: 2.7s
- Isolated avg TTFT: 1.73s
- Result: +56% (shared WORSE)
- Root cause: 8 concurrent DMA streams saturate PCIe 4.0 uplink: 15 GB/s / 8 = 1.9 GB/s per stream, single DMA inflates from 85ms to ~750ms
- Verdict: Burst is unrealistic workload; staggered/normal serving load unaffected

### MLA+TP8 (Prefill Too Cheap)

- Shared avg TTFT: 0.184s
- Isolated avg TTFT: 0.187s
- Result: +1.6% (no meaningful gain)
- Root cause: MLA kv_lora_rank=512 compresses KV compute to ~100ms; DMA of compressed KV (~40 MB) takes ~3ms; prefill cost too small to save
- Verdict: PegaFlow requires large enough prefill gap to overcome DMA cost. 16B MLA model does not meet threshold; 236B+ may.


## Producer (Warmup Seed) Records
- Count: 6
- Median TTFT: 1.0641s
- Mean TTFT: 1.0657s
- These records are excluded from consumer paired-delta analysis.
- They seed the shared cache but are not themselves cross-instance consumers.

## Evidence Violations (Fail-Close)
- None — all connector/prefetch/DMA events unique and conserved.

## Validity Manifest
- Run ID: 20260813-090821
- Total records: 96
- Consumer shared records: 45
- Consumer isolated records: 45
- Producer records: 6
- INVALID records: 0
- Audit-invalid records (evidence): 0
- Conservation: OK (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback-only DMA=0)
- Validity gate: PASS
- Audit verdict: VALID

## Artifacts
- Raw records: `/home/cyb/pegaflow-hust/results/trace-audit/20260813-090821/trace_audit.json`
- Per-arm server logs: `/home/cyb/pegaflow-hust/results/trace-audit/20260813-090821/logs/arm_*/server.log`
- vLLM logs: `/home/cyb/pegaflow-hust/results/trace-audit/20260813-090821/logs/vllm_*.log`
- Environment snapshot: `trace_audit.json` → `_env` key
