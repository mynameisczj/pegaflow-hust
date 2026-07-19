1#!/bin/bash
# ============================================================================
# PegaFlow Prefix-Caching Performance Benchmark
#
# Compares vLLM serving throughput/TTFT with and without PegaFlow KV cache
# offloading, using the vllm bench serve CLI and PegaFlow's Prometheus metrics.
#
# The benchmark runs two configurations back-to-back on the same model:
#   BASELINE: vllm serve without PegaFlow (pure local KV cache)
#   PEGAFLOW: vllm serve + PegaKVConnector (external KV cache offload)
#
# Metrics collected:
#   - TTFT (time-to-first-token) p50/p95/p99 from vllm bench serve
#   - Throughput (tokens/sec) from vllm bench serve
#   - PegaFlow save/load bytes and cache hit rate from :9091/metrics
#   - NPU memory usage from npu-smi
#
# Usage:
#   ./scripts/bench_pegaflow.sh [NPU_DEVICE_ID]
#
# Dependencies:
#   - Ascend NPU + CANN runtime
#   - Built pegaflow-server-py binary
#   - vllm-hust Python venv with pegaflow connector installed
#   - Qwen2.5-0.5B-Instruct model cached locally
# ============================================================================

set -euo pipefail

# Ascend aclrtMallocHost requires locked memory for DMA-pinned allocations.
# Container defaults may cap this at 64KB; raise it before starting.
ulimit -l unlimited

NPU_DEVICE="${1:-2}"
GRPC_PORT=50059
VLLM_PORT=8100
TAG="bench-$(date +%Y%m%d-%H%M%S)"
RESULTS_DIR="/tmp/pegaflow-bench-${TAG}"

# Model selection — Qwen2.5-0.5B for fast iteration.
MODEL="/root/.cache/modelscope/models/qwen--Qwen2.5-0.5B-Instruct/snapshots/master"

# Benchmark workload parameters.
NUM_PROMPTS="${NUM_PROMPTS:-100}"
INPUT_LEN="${INPUT_LEN:-512}"
OUTPUT_LEN="${OUTPUT_LEN:-128}"
CONCURRENCY="${CONCURRENCY:-8}"
PREFIX_REUSE_RATIO="${PREFIX_REUSE_RATIO:-0.8}"

# Resolve paths.
ASCEND_HOME="${ASCEND_HOME_PATH:-/usr/local/Ascend/cann-8.5.1}"
ASCEND_DRIVER="${ASCEND_HOME_PATH:+$(dirname "$ASCEND_HOME_PATH")/driver}/lib64/driver"
ASCEND_DRIVER="${ASCEND_DRIVER:-/usr/local/Ascend/driver/lib64/driver}"
ATB_LIB=$(ls -d /usr/local/Ascend/nnal/atb/*/atb/cxx_abi_1/lib 2>/dev/null | head -1)
ATB_LIB="${ATB_LIB:-/usr/local/Ascend/nnal/atb/8.5.1/atb/cxx_abi_1/lib}"
VENV_DIR="${PEGAFLOW_VENV:-/root/miniconda3/envs/vllm-hust-dev}"
PYTHON="${VENV_DIR}/bin/python"
PEGAFLOW_DIR="/workspace/pegaflow-hust"
CARGO_TARGET="${PEGAFLOW_DIR}/target/debug"
SERVER_LOG="/tmp/pf-bench-server-${TAG}.log"
VLLM_LOG="/tmp/pf-bench-vllm-${TAG}.log"

export LD_LIBRARY_PATH="\
${VENV_DIR}/lib:\
${ASCEND_HOME}/lib64:\
${ASCEND_HOME}/aarch64-linux/lib64:\
${ASCEND_DRIVER}:\
${ATB_LIB}"
export ASCEND_VISIBLE_DEVICES="${NPU_DEVICE}"
export VLLM_PLUGINS=ascend
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export PYTHONHASHSEED=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

health_check() {
  local url="$1" timeout="${2:-5}"
  "${PYTHON}" -c "
import urllib.request, sys
try:
    resp = urllib.request.urlopen('${url}', timeout=${timeout})
    resp.read()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null
}

fetch_metric() {
  # Fetch a single Prometheus metric value by name from a metrics endpoint.
  local url="$1" name="$2"
  "${PYTHON}" -c "
import urllib.request
r = urllib.request.urlopen('${url}')
for l in r.read().decode().split('\n'):
    l = l.strip()
    if '${name}' in l and not l.startswith('#'):
        print(l.split()[-1])
        break
" 2>/dev/null || echo "0"
}

npufree_mb() {
  npu-smi info 2>/dev/null \
    | grep "^\s*|\s*${NPU_DEVICE}\s" \
    | awk -F'|' '{print $8}' \
    | tr -d ' /' \
    || echo "N/A"
}

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

cleanup_all() {
  echo "  [cleanup] stopping processes..."
  kill ${VLLM_PID:-} 2>/dev/null || true
  wait ${VLLM_PID:-} 2>/dev/null || true
  if [ -n "${SERVER_PID:-}" ] && kill -0 ${SERVER_PID} 2>/dev/null; then
    kill ${SERVER_PID} 2>/dev/null || true
    wait ${SERVER_PID} 2>/dev/null || true
  fi
  pkill -9 -f "pegaflow-server-py"   2>/dev/null || true
  pkill -9 -f "vllm.entrypoints"     2>/dev/null || true
  pkill -9 -f "EngineCore"           2>/dev/null || true
  pkill -9 -f "multiprocessing.resource_tracker" 2>/dev/null || true
  sleep 2
}

trap cleanup_all EXIT

mkdir -p "${RESULTS_DIR}"

echo "============================================================"
echo " PegaFlow Prefix-Caching Benchmark"
echo " NPU: ${NPU_DEVICE}  Model: Qwen2.5-0.5B-Instruct"
echo " Tag: ${TAG}"
echo " Num prompts: ${NUM_PROMPTS}  Input len: ${INPUT_LEN}"
echo " Output len: ${OUTPUT_LEN}  Concurrency: ${CONCURRENCY}"
echo " Results: ${RESULTS_DIR}"
echo "============================================================"

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
echo ""
echo "[1/8] Building pegaflow..."
cd "${PEGAFLOW_DIR}"
PYO3_PYTHON="${PYTHON}" cargo build --no-default-features --features ascend \
  -p pegaflow-py --lib --bin pegaflow-server-py 2>&1 | tail -3
\cp -f "${CARGO_TARGET}/libpegaflow.so" \
  "${PEGAFLOW_DIR}/python/pegaflow/pegaflow.cpython-311-aarch64-linux-gnu.so"
echo "  Build OK"

# ---------------------------------------------------------------------------
# Phase A: BASELINE (vllm without PegaFlow)
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Phase A: BASELINE (native vLLM, no external KV cache)"
echo "============================================================"

cleanup_all

VLLM_BASE_ARGS=(
  --model "${MODEL}"
  --port "${VLLM_PORT}"
  --max-model-len $((INPUT_LEN + OUTPUT_LEN + 256))
  --gpu-memory-utilization 0.1
  --enforce-eager
)

echo "[2/8] Starting vLLM (baseline)..."
nohup "${PYTHON}" -m vllm.entrypoints.openai.api_server "${VLLM_BASE_ARGS[@]}" \
  > "${VLLM_LOG}" 2>&1 &
VLLM_PID=$!
disown ${VLLM_PID} 2>/dev/null || true

for i in $(seq 1 180); do
  if health_check "http://127.0.0.1:${VLLM_PORT}/health"; then
    echo "  vLLM ready (${i}s)"
    break
  fi
  if ! kill -0 ${VLLM_PID} 2>/dev/null; then
    echo "  FAIL: vLLM crashed."; tail -30 "${VLLM_LOG}"; exit 1
  fi
  sleep 3
done

echo "  NPU free: $(npufree_mb) MB"

# Run benchmark
echo "[3/8] Running baseline benchmark..."
BASELINE_OUT="${RESULTS_DIR}/baseline_serve.json"
"${PYTHON}" -m vllm.entrypoints.cli.main bench serve \
  --backend openai-chat \
  --base-url "http://127.0.0.1:${VLLM_PORT}" \
  --model "${MODEL}" \
  --endpoint /v1/chat/completions \
  --num-prompts "${NUM_PROMPTS}" \
  --max-concurrency "${CONCURRENCY}" \
  --save-result \
  --result-dir "${RESULTS_DIR}" \
  --result-filename "$(basename "${BASELINE_OUT}")" \
  2>&1 | tee "${RESULTS_DIR}/baseline_bench.log"

BASELINE_NPU_AFTER=$(npufree_mb)

cleanup_all

# ---------------------------------------------------------------------------
# Phase B: PEGAFLOW (vllm + PegaFlow external KV cache)
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Phase B: PEGAFLOW (vllm + PegaKVConnector)"
echo "============================================================"

echo "[4/8] Starting pegaflow-server..."
nohup "${CARGO_TARGET}/pegaflow-server-py" \
  --addr "127.0.0.1:${GRPC_PORT}" \
  --devices "${NPU_DEVICE}" \
  --pool-size 2gb \
  > "${SERVER_LOG}" 2>&1 &
SERVER_PID=$!
disown ${SERVER_PID} 2>/dev/null || true

for i in $(seq 1 30); do
  if health_check "http://127.0.0.1:9091/health"; then
    echo "  Server ready (${i}s)"
    break
  fi
  if ! kill -0 ${SERVER_PID} 2>/dev/null; then
    echo "  FAIL: Server crashed."; tail -20 "${SERVER_LOG}"; exit 1
  fi
  sleep 1
done

echo "[5/8] Starting vLLM (PegaFlow)..."
KV_CONFIG=$(cat <<EOF
{"kv_connector":"PegaKVConnector","kv_role":"kv_both","kv_connector_module_path":"pegaflow.connector","kv_connector_extra_config":{"pegaflow.port":${GRPC_PORT}}}
EOF
)

nohup "${PYTHON}" -m vllm.entrypoints.openai.api_server \
  "${VLLM_BASE_ARGS[@]}" \
  --kv-transfer-config "${KV_CONFIG}" \
  > "${VLLM_LOG}" 2>&1 &
VLLM_PID=$!
disown ${VLLM_PID} 2>/dev/null || true

for i in $(seq 1 180); do
  if health_check "http://127.0.0.1:${VLLM_PORT}/health"; then
    echo "  vLLM ready (${i}s)"
    break
  fi
  if ! kill -0 ${VLLM_PID} 2>/dev/null; then
    echo "  FAIL: vLLM crashed."; tail -30 "${VLLM_LOG}"; exit 1
  fi
  sleep 3
done

echo "  NPU free: $(npufree_mb) MB"

# Warmup round: fill PegaFlow cache
echo "[6/8] Warmup round (filling PegaFlow cache)..."
"${PYTHON}" -m vllm.entrypoints.cli.main bench serve \
  --backend openai-chat \
  --base-url "http://127.0.0.1:${VLLM_PORT}" \
  --model "${MODEL}" \
  --endpoint /v1/chat/completions \
  --num-prompts $((NUM_PROMPTS / 2)) \
  --max-concurrency "${CONCURRENCY}" \
  2>&1 | tail -5

sleep 5

# Collect pre-benchmark PegaFlow metrics
PF_SAVE_BEFORE=$(fetch_metric "http://127.0.0.1:9091/metrics" "save_bytes_total")
PF_LOAD_BEFORE=$(fetch_metric "http://127.0.0.1:9091/metrics" "load_bytes_total")
PF_BLOCKS_BEFORE=$(fetch_metric "http://127.0.0.1:9091/metrics" "pegaflow_cache_block_insertions")

echo "  Pre-benchmark PegaFlow state:"
echo "    save_bytes_total=${PF_SAVE_BEFORE}"
echo "    load_bytes_total=${PF_LOAD_BEFORE}"
echo "    cache_blocks=${PF_BLOCKS_BEFORE}"

# Run benchmark with PegaFlow
echo "[7/8] Running PegaFlow benchmark..."
PEGAFLOW_OUT="${RESULTS_DIR}/pegaflow_serve.json"
"${PYTHON}" -m vllm.entrypoints.cli.main bench serve \
  --backend openai-chat \
  --base-url "http://127.0.0.1:${VLLM_PORT}" \
  --model "${MODEL}" \
  --endpoint /v1/chat/completions \
  --num-prompts "${NUM_PROMPTS}" \
  --max-concurrency "${CONCURRENCY}" \
  --save-result \
  --result-dir "${RESULTS_DIR}" \
  --result-filename "$(basename "${PEGAFLOW_OUT}")" \
  2>&1 | tee "${RESULTS_DIR}/pegaflow_bench.log"

# Collect post-benchmark PegaFlow metrics
PF_SAVE_AFTER=$(fetch_metric "http://127.0.0.1:9091/metrics" "save_bytes_total")
PF_LOAD_AFTER=$(fetch_metric "http://127.0.0.1:9091/metrics" "load_bytes_total")
PF_BLOCKS_AFTER=$(fetch_metric "http://127.0.0.1:9091/metrics" "pegaflow_cache_block_insertions")
PF_HITS=$(fetch_metric "http://127.0.0.1:9091/metrics" "pegaflow_cache_hits_total")
PF_MISSES=$(fetch_metric "http://127.0.0.1:9091/metrics" "pegaflow_cache_misses_total")
PEGAFLOW_NPU_AFTER=$(npufree_mb)

echo "  Post-benchmark PegaFlow state:"
echo "    save_bytes_total=${PF_SAVE_AFTER}"
echo "    load_bytes_total=${PF_LOAD_AFTER}"
echo "    cache_blocks=${PF_BLOCKS_AFTER}"
echo "    hits=${PF_HITS}  misses=${PF_MISSES}"

# ---------------------------------------------------------------------------
# Phase C: Collect & compare results
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Phase C: Results Summary"
echo "============================================================"

echo "[8/8] Generating report..."

REPORT="${RESULTS_DIR}/report.md"

"${PYTHON}" -c "
import json, os, sys

results_dir = '${RESULTS_DIR}'
baseline_file = os.path.join(results_dir, 'baseline_serve.json')
pegaflow_file = os.path.join(results_dir, 'pegaflow_serve.json')

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {'error': str(e)}

baseline = load_json(baseline_file)
pegaflow = load_json(pegaflow_file)

def safe_num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

lines = []
lines.append('# PegaFlow Prefix-Caching Benchmark Report')
lines.append('')
lines.append(f'**Tag:** ${TAG}  ')
lines.append(f'**Model:** Qwen2.5-0.5B-Instruct  ')
lines.append(f'**Prompts:** ${NUM_PROMPTS}  ')
lines.append(f'**Input/Output len:** ${INPUT_LEN}/${OUTPUT_LEN}  ')
lines.append(f'**Concurrency:** ${CONCURRENCY}  ')
lines.append('')

# TTFT / Throughput comparison
lines.append('## vLLM Serving Performance')
lines.append('')
lines.append('| Metric | Baseline | PegaFlow | Delta |')
lines.append('|--------|----------|----------|-------|')

for metric_key, label in [
    ('mean_ttft_ms', 'TTFT mean (ms)'),
    ('median_ttft_ms', 'TTFT p50 (ms)'),
    ('p99_ttft_ms', 'TTFT p99 (ms)'),
    ('mean_tpot_ms', 'TPOT mean (ms)'),
    ('median_tpot_ms', 'TPOT median (ms)'),
    ('request_throughput', 'Throughput (req/s)'),
    ('output_throughput', 'Output TPS'),
]:
    b_val = safe_num(baseline.get(metric_key)) if isinstance(baseline, dict) else 0.0
    p_val = safe_num(pegaflow.get(metric_key)) if isinstance(pegaflow, dict) else 0.0
    if b_val > 0:
        delta_pct = (p_val - b_val) / b_val * 100
    else:
        delta_pct = float('nan')
    lines.append(f'| {label} | {b_val:.2f} | {p_val:.2f} | {delta_pct:+.1f}% |')

lines.append('')

# PegaFlow metrics
lines.append('## PegaFlow KV Cache Metrics')
lines.append('')
save_delta = safe_num(${PF_SAVE_AFTER}) - safe_num(${PF_SAVE_BEFORE})
load_delta = safe_num(${PF_LOAD_AFTER}) - safe_num(${PF_LOAD_BEFORE})
blocks_delta = safe_num(${PF_BLOCKS_AFTER}) - safe_num(${PF_BLOCKS_BEFORE})

lines.append('| Metric | Before | After | Delta |')
lines.append('|--------|--------|-------|-------|')
lines.append(f'| save_bytes_total | ${PF_SAVE_BEFORE} | ${PF_SAVE_AFTER} | {save_delta} |')
lines.append(f'| load_bytes_total | ${PF_LOAD_BEFORE} | ${PF_LOAD_AFTER} | {load_delta} |')
lines.append(f'| cache_blocks | ${PF_BLOCKS_BEFORE} | ${PF_BLOCKS_AFTER} | {blocks_delta} |')
lines.append(f'| cache_hits_total | — | ${PF_HITS} | — |')
lines.append(f'| cache_misses_total | — | ${PF_MISSES} | — |')
lines.append('')

# NPU memory
lines.append('## NPU Memory')
lines.append('')
lines.append('| Phase | Free (MB) |')
lines.append('|-------|-----------|')
lines.append(f'| Baseline (after) | ${BASELINE_NPU_AFTER} |')
lines.append(f'| PegaFlow (after) | ${PEGAFLOW_NPU_AFTER} |')
lines.append('')

# Raw metrics files
lines.append('## Raw Output Files')
lines.append('')
for name in ['baseline_serve.json', 'pegaflow_serve.json',
             'baseline_bench.log', 'pegaflow_bench.log']:
    lines.append(f'- `{name}`')
lines.append('')

report = '\n'.join(lines)
print(report)
with open('${REPORT}', 'w') as f:
    f.write(report)
print(f'Report written to ${REPORT}')
" 2>&1

echo ""
echo "============================================================"
echo " Benchmark Complete: ${TAG}"
echo " Results: ${RESULTS_DIR}"
echo " Report:  ${REPORT}"
echo " Server log: ${SERVER_LOG}"
echo " vLLM log:   ${VLLM_LOG}"
echo "============================================================"
