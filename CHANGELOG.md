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

## 2026-08-18 — T1 baseline: first 8-instance VALID matched trace

- `results/perf-t1/20260818-090625/` — T1 baseline, 3 cycles × 8 instances
  × 3 queries, Qwen3-8B, vllm-hust@HEAD, commit 021473b. Audit verdict
  **VALID** (100% coverage, conservation OK, 0 violations, 144 records).
  Raw logs gitignored (`results/perf-t1/*/logs/`); manifest committed.
- Q0 (cross-instance): shared median 0.356s vs isolated 0.938s —
  prefill saved +581.7ms, DMA cost 120.1ms → **GO** (CI excludes 0).
- Q2: +58.3ms vs 3.5ms → **GO**. Q1: BREAK-EVEN (local prefix hit, expected).
- TBT p95: 18.8ms both arms (no decode-path regression; TBT gate PASS).
- Platform constraint recorded (prereg deviation C): 216 D2H + 42 H2D
  batch calls fell back to per-copy (CANN batch 107000 on 8-instance
  concurrency); completions data-correct. D2H chunking tracked.
- Earlier runs today (072129/075403/083342) INVALID — retained locally as
  negative evidence of the platform constraint, not committed.

## 2026-08-18 — T1 rerun: batch DMA restored (allocator contract)

- `results/perf-t1/20260818-104618/` — T1 rerun with
  `PYTORCH_NPU_ALLOC_CONF=expandable_segments:True` + chunked batch defense.
  Audit verdict **VALID**, 0 batch fallbacks (platform-constraint section
  absent from manifest), conservation OK, 144 records.
- Q0: shared 0.328s vs isolated 0.937s, prefill saved +609.1ms, DMA cost
  90.5ms (vs 120.1ms under per-copy fallback in run 20260818-090625) → **GO**,
  CI [531.6, 535.5]ms excludes 0.
- DMA cost now matches the 20260813 5-instance VALID run (89ms) — batch
  aclrtMemcpyBatchAsync (5472 copies, 71-101ms) fully restored.
- Confirms root cause: torch_npu default-allocator memory is not batch-DMA
  capable; expandable_segments memory is (comment "expandable_segments is
  not DMA-capable" is outdated).

## 2026-08-18 — T2 concurrency gradient: 9/9 combos VALID, no contention point

- `results/perf-t2-c{1,4,8}-i{0,50,200}/` — 9 combos, one cycle each,
  semaphore-limited concurrent sends. All **VALID**, 0 batch fallbacks.
- Q0 (cross-instance) per combo:
  - concurrency 1: saved ~611ms, DMA ~92ms
  - concurrency 4: saved ~577ms, DMA ~122ms
  - concurrency 8: saved ~556ms, DMA ~147ms
- Batch interval (0/50/200ms) has no measurable effect; DMA cost scales
  with concurrency only. All combos **GO** — no contention knee within the
  scanned range (8-way DMA 147ms is far below the ~556ms prefill saving).
- Safe operating region: concurrency <= 8 (full scanned range). Burst
  negative example (32 requests, unlimited semaphore, +56%) still stands
  as the pathological boundary.
- Harness robustness fixes landed during the sweep (all host-verified):
  empty req_id no longer duplicate-matches all connector keys; startup
  retry (1x) for slow engine init; kill_tracked kills descendant processes
  (vLLM EngineCore spawns a new process group); launch timeout 900s.

## 2026-08-18 — INVALID runs archived as platform-constraint negative evidence

- `results/perf-t1/20260818-{072129,075403,083342}/` — three INVALID T1
  runs preserved per prereg §8 (negative-example retention): 072129
  (default-allocator batch 107000 -> fallback evidence rules),
  075403 (same, chunked-batch defense), 083342 (fallback direction
  disambiguation). Manifests document the INVALID verdicts; raw logs
  gitignored. Superseded by the VALID runs (090625, 104618).

## 2026-08-18 — T3/T4 runners

- `scripts/run_perf_t3_hitrate.py`: hit-rate sensitivity (50/75/90/100%).
  Prefix-ratio manipulation: warmup seeds full prompt, Q0 test keeps the
  first ratio% identical + distinct filler (total length unchanged). Gate:
  measured hit_blocks/76 within +/-5pp of target, else INVALID.
- `scripts/run_perf_t4_len.py`: prompt-length gradient (1k/4k/8k/16k tokens)
  via block repetition (chars/4 proxy).
- `scripts/run_perf_base.py`: `Experiment.prompt_fn(query, query_idx)` for
  custom prompt construction (query_idx -1 = warmup seed); dry-run skips
  experiment-specific gates (synthetic records are 100%-hit; gates are
  unit-tested instead).
- Host gates: dry-run VALID for both runners; T3 hitrate gate unit-tested
  (passes at target, fails off-target).
