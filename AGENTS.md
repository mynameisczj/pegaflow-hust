# PegaFlow Agent Guide

This file provides guidance for agents working in the PegaFlow repository.

## Project Overview

PegaFlow is a high-performance KV cache transfer system for LLM inference (vLLM). It offloads KV cache from GPU to host memory/SSD and shares it across nodes via RDMA.

## Workspace Layout

```text
pegaflow/
├── pegaflow-common/       # Shared utilities (logging, NUMA)
├── pegaflow-core/         # Core engine: storage, transfer, backing store
├── pegaflow-proto/        # Protobuf and gRPC definitions (prost/tonic)
├── pegaflow-server/       # gRPC server, router, HTTP metrics/health
├── pegaflow-metaserver/   # Cross-node block hash registry
├── pegaflow-transfer/     # RDMA transfer engine (Mooncake-compatible)
├── pegaflow-pd-wire/      # P/D disaggregation wire protocol
├── python/                # PyO3 bindings + vLLM connector (published as `pegaflow-llm`)
├── examples/              # Python examples and benchmarks
├── scripts/               # Build/check/bench helper scripts
└── prek.toml              # Local pre-commit/check configuration
```

`src/main.rs` is a placeholder; real binaries live in `pegaflow-server/src/bin/`, `pegaflow-metaserver/src/bin/`, and `python/src/bin/`.

## Key Entry Points

| Component | Entry |
|-----------|-------|
| Main engine | `pegaflow-core/src/lib.rs` |
| Storage pipeline | `pegaflow-core/src/storage/mod.rs` |
| SSD backing | `pegaflow-core/src/backing/ssd.rs` |
| Cross-node coordination | `pegaflow-core/src/internode/metaserver_client.rs` |
| gRPC service | `pegaflow-server/src/service.rs` |
| HTTP metrics/health | `pegaflow-server/src/http_server.rs` |
| MetaServer registry | `pegaflow-metaserver/src/service.rs`, `pegaflow-metaserver/src/store.rs` |
| RDMA engine | `pegaflow-transfer/src/engine.rs` |
| PyO3 bindings | `python/src/lib.rs` |
| vLLM connector (scheduler) | `python/pegaflow/connector/scheduler.py` |
| vLLM connector (worker) | `python/pegaflow/connector/worker.py` |
| Python type stubs | `python/pegaflow/pegaflow.pyi` |

## Build, Check, Test

### Rust

```bash
cargo build
cargo build --release
cargo test --release --no-default-features --features cuda-13,rdma
```

Default features target CUDA 12. On CUDA 13 machines, always pass `--no-default-features --features cuda-13,rdma` to `cargo test` and `cargo clippy` or you'll get missing `libcudart` symbol errors.

The CI clippy excludes `pegaflow-py`: `cargo clippy --workspace --exclude pegaflow-py --all-targets -- -D warnings`. Local `prek` clippy does not exclude it.

### Python Bindings

```bash
cd python
maturin develop
maturin develop --release
# CUDA 13:
uv run maturin develop -r --no-default-features --features cuda-13
```

### Local Checks

```bash
prek run
./scripts/check.sh        # Alternative: fmt, typos, ruff, clippy, cargo check
```

`prek run` fails on `master`/`main` due to the `no-commit-to-branch` hook. Work on a feature branch.

`prek` runs: trailing-whitespace, end-of-file-fixer, large-files check, merge-conflict check, typos, codespell (Python), isort (Python), ruff (check + format), cargo fmt, cargo clippy (CUDA 13 features), and `cargo test --release` (CUDA 13 features).

### Python Test Gates

| Gate | Command | Notes |
|------|---------|-------|
| Default unit | `cd python && uv run --extra test pytest` | No GPU, no vLLM, no server. |
| Source-only default (CI) | `cd python && uv run --isolated --no-project --with pytest --with numpy --with 'requests>=2.26.0' pytest` | Proves no torch/vLLM/CUDA needed. |
| Integration | `cd python && uv run --extra test pytest -m integration` | Needs native extension + server binary + GPU. |
| E2E | `cd python && uv run --extra test pytest -m e2e tests/test_vllm_e2e_correctness.py --model /data/models/Qwen3-4B --max-model-len 4096` | Merge-before gate. |
| Stress | `cd python && uv run --extra test pytest -m stress tests/test_vllm_warm_hit_stress.py --model /data/models/Qwen3-4B --max-model-len 2048` | Targeted pressure evidence. |
| Release smoke | See `python/tests/README.md` | Validates installed artifact. |

The default pytest config in `python/pyproject.toml` filters out integration, e2e, stress, and gpu markers: `-m "not integration and not e2e and not stress and not gpu"`.

Do not default to running all of `python/tests`. Do not add an `xtask` wrapper.

### Version Consistency

`Cargo.toml` `[workspace.package] version`, `python/pyproject.toml` `[project] version`, and `python/pyproject.toml` `[tool.commitizen] version` must always match. CI enforces this.

## Compatibility & Durability

- **Strict version handshake**: `CARGO_PKG_VERSION` exact match at registration. No backward compatibility — bump the version and break freely.
- **SSD cache is ephemeral**: wiped on restart. No migration, on-disk versioning, or cross-version SSD compatibility.

## Environment Variables

- `PEGAFLOW_ENGINE_ENDPOINT` — gRPC endpoint (default: `127.0.0.1:50055`)
- `PEGAFLOW_INSTANCE_ID` — Override instance ID
- `RUST_LOG` — Rust logging (e.g., `info,pegaflow_core=debug,pegaflow_server=debug`)

## Run Services

```bash
cargo run -r --bin pegaflow-server -- --addr 0.0.0.0:50055 --pool-size 30gb
cargo run -r --bin pegaflow-metaserver
```

After `maturin develop`, the Python console scripts `pegaflow-server` and `pegaflow-metaserver` are also available.

## Code Style

### General

- Use English in comments.
- Use `.venv` for the Python virtual environment.
- Code should be self-documenting. If a comment seems necessary, first try refactoring.

### Rust

- Visibility: `fn` > `pub(crate)` > `pub`.
- Prefer explicit errors over `unwrap`/`expect`.
- `use` ordering: std, external crates, local crate.
- Prefer `NonNull` over raw pointers in unsafe code.
- Edition 2024, resolver 2.

### Python (3.10+)

- Native generics: `list`, `dict`, `set`, `tuple` (not `typing.List` etc.).
- PEP 604 unions: `X | None` (not `Optional[X]`).
- Logging: `%s` formatting (`logger.info("x=%s", x)`) — not f-strings.
- Imports: standard library, third-party, local.
- Ruff line-length 100, targets py310, selects E/F/W/I/UP/B/C4/SIM, ignores E501.

### PyO3

- Keep Python-facing APIs thin; delegate core logic to Rust crates.
- Convert Rust errors to `PyErr` cleanly.
- When modifying `python/src/lib.rs`, update `python/pegaflow/pegaflow.pyi`.

## Testing Principles

- Don't add tests just for the sake of adding tests. Would skipping this test materially reduce merge confidence? If not, delete it.
- Prefer table-driven cases with clear ids over copy-pasted methods.
- Default Python tests: fast, stable, no GPU, no vLLM, no native extension build.
- Heavy tests must declare their marker: integration, e2e, stress, or release smoke. A heavy test without a marker should not live in the main pytest surface.
- Stub/mock tests: allowed for local contracts only; must not shadow real runtime modules during integration/e2e collection.

## Git Workflow

- Do not commit directly to `master`.
- Branch naming: `feat/`, `fix/`, `chore/`, `refactor/`, `style/`, `ci/`.
- Conventional Commits via Commitizen: use `cz c` for interactive commits.
- `prek` hooks enforce: no-commit-to-branch (master/main), formatting, typos, lint, tests.
