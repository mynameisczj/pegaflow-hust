# T2: concurrency=4 interval=200ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T14:46:01+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 0 | **0.0000** | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 0.0000 |
| Isolated | 0 | **0.0000** | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 0.0000 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 0 | **0.0000** | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 0.0000 |
| Isolated | 0 | **0.0000** | 0.0000 | 0.0000 | [0.0000, 0.0000] | 0.0000 | 0.0000 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

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

- Coverage gate FAILED: 0.0% (requires 100%)
## Evidence Violations (Fail-Close)

- [INVALID] missing connector event: req=
- [INVALID] missing connector event: req=
- [INVALID] missing connector event: req=
- [INVALID] missing connector event: req=
- [INVALID] missing connector event: req=
- [INVALID] missing connector event: req=
- [INVALID] NPU3 owner drift: foreign pid=1412263 attached to admitted device
- [INVALID] NPU4 owner drift: foreign pid=1412264 attached to admitted device

## Validity Manifest
- Run ID: 20260818-144550
- Total records: 6
- Consumer shared records: 0
- Consumer isolated records: 0
- Producer records: 0
- INVALID records: 6
- Audit-invalid records (evidence): 6
- Conservation: BROKEN (connector dup=0, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: FAIL
- Audit verdict: INVALID

## Reproduce
- Command: `python scripts/run_perf_t2-c4-i200_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

