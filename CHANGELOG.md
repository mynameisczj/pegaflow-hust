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
- Active scripts now: `run_trace_audit.py`, `test_trace_audit_dryrun.py`
  (repo root), `scripts/build-wheel.sh`, `scripts/check.sh`.
- Docs (outside repo, not committed): NPU migration status
  (`/workspace/HUST/npu_migration_status.md`), perf test plan
  (`/workspace/HUST/pegaflow-perf-test-plan.md`).
