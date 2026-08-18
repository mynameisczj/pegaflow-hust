# Changelog

## Unreleased

- Align `pegaflow-hust` with the workspace repository contract.

## 2026-08-18 — performance-test process standardization (part 1: cleanup)

- Archive 14 legacy test scripts into `_archived_scripts/` (kept for
  reference, not run — see `_archived_scripts/README.md` for supersession
  mapping):
  - Moved from repo root: `run_bench_8inst.py`,
    `run_bench_8inst_concurrent.py`, `run_bench_mla_tp8_concurrent.py`
    (superseded by trace-audit matched methodology and the planned perf
    harness).
  - Moved from `scripts/`: `bench_multi_baseline.sh`,
    `bench_multi_pegaflow.sh`, `bench_pegaflow.sh`,
    `bench_pegaflow_multi.sh`, `run_vllm_ttft_bench.sh`,
    `diagnose_fork_socket.py`, `diagnose_vllm_tcp.sh`,
    `run_nixl_local.sh`, `run_pd_local.sh`, `pd_rdma_binding_probe.py`,
    `pd_rdma_e2e.py` (one-off diagnostics, superseded benchmarks, and
    pd/nixl helpers awaiting an NPU e2e gate).
- `ruff.toml`: drop excludes for moved benchmark scripts; add
  `_archived_scripts/` to `extend-exclude`.
- Archive `benchmark_report.md` → `_archived_docs/` (historical benchmark
  results superseded by the 20260813 VALID matched trace; see
  `_archived_docs/README.md`).
- Active scripts now: `run_trace_audit.py`, `test_trace_audit_dryrun.py`
  (repo root), `scripts/build-wheel.sh`, `scripts/check.sh`.
- Docs (outside repo, not committed): NPU migration status
  (`/workspace/HUST/npu_migration_status.md`), perf test plan
  (`/workspace/HUST/pegaflow-perf-test-plan.md`).

## 2026-08-18 — perf harness W1 (standardized test flow)

- Add `scripts/run_perf_base.py`: shared harness extracted from
  `run_trace_audit.py` — run-id artifacts, env snapshot (incl. torch/torch_npu
  versions + ascend commit), matched AB/BA arms, independent lifecycle,
  fail-close evidence gates, per-query-class paired analysis, TBT/TPOT token
  timestamps, `--dry-run` host gate, `--verify-repro` reproducibility gate
  (perf plan §9.1).
- Add `scripts/run_perf_t1_baseline.py`: T1 experiment (Qwen3-8B, 8 instances,
  3 cycles) with TBT stability gate (shared p95 ≤ isolated p95 × 1.10).
- Instrument `python/pegaflow/npu_ipc_wrapper.py`: `exported_at` / `imported_at`
  wall-clock timestamps (backward-compatible 6-tuple pickles still load).
- Instrument `pegaflow-server/src/registry.rs`: `IPC import timing` log line in
  `materialize_tensor` (import_ms per tensor). Rust change not compile-verified
  locally (no cargo on host) — CI `cargo check (ascend)` is the gate.
- Deferred: prefetch queue-depth instrumentation (needs server-side metrics
  design; prefetch→DMA gap already derivable from existing logs).
- Host gates verified locally: T1 `--dry-run` → VALID, coverage 100%,
  conservation OK; TBT gate fires on regression and passes on healthy data.

## 2026-08-18 — perf harness fix: fallback DMA evidence + direction disambiguation

- `scripts/run_perf_base.py` (prereg deviation C, recorded):
  - Fallback WARN lines and the subsequent completion line are the SAME
    transfer — fallback lines are platform-constraint stats only; the
    `Load task completed` line is the formal evidence.
  - Direction disambiguation: D2H fallback = save-path (counted in
    manifest, never bound); H2D fallback = load-path (completion still
    formal evidence).
  - Platform reality on 8-instance concurrency: CANN
    `aclrtMemcpyBatchAsync` intermittently fails 107000 on both directions;
    per-copy fallback completes correctly (data-verified). Batch DMA
    recovery (D2H chunking) is a tracked follow-up.
- `scripts/run_perf_base.py`: container-aware npu-smi PID parsing
  (uses "Process id in container" column — host PIDs are invisible inside
  the container); vLLM start deadline 180s → 420s (8-instance concurrent
  engine init measured 129s single-instance).
- `pegaflow-server/src/registry.rs`: compile fix for IPC import timing log
  (adjacent string literals need explicit concatenation).
