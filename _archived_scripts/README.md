# Archived Scripts

Legacy scripts moved here on 2026-08-18 during performance-test process
standardization (see CHANGELOG.md). Kept for reference only — **do not use,
do not run**. Git history preserves their prior versions.

Reason for each move:

| File | Superseded by |
|---|---|
| `run_bench_8inst.py` | trace-audit methodology + planned perf harness (perf plan T1) |
| `run_bench_8inst_concurrent.py` | trace-audit staggered-concurrency results (20260813 VALID) |
| `run_bench_mla_tp8_concurrent.py` | perf plan T6 (MLA extension) |
| `bench_multi_baseline.sh` / `bench_multi_pegaflow.sh` / `bench_pegaflow.sh` / `bench_pegaflow_multi.sh` | `run_trace_audit.py` (matched arms) |
| `run_vllm_ttft_bench.sh` | `run_trace_audit.py` |
| `diagnose_fork_socket.py` / `diagnose_vllm_tcp.sh` | one-off diagnostics, no longer referenced |
| `run_nixl_local.sh` / `run_pd_local.sh` | pd/nixl paths unverified on NPU (perf plan T7/T8); archived until an NPU e2e gate exists |
| `pd_rdma_binding_probe.py` / `pd_rdma_e2e.py` | same as above |
