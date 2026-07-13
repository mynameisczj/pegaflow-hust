#!/bin/bash
# ============================================================================
# PegaFlow + vLLM 端到端集成验证脚本
#
# 验证 vLLM 与 PegaFlow connector 的完整集成:
#   1. 编译 + 启动 pegaflow-server
#   2. 启动 vLLM API server (加载 PegaKVConnector)
#   3. 发送请求触发 KV cache save
#   4. 检查 pegaflow 指标确认 save 成功
#
# 用法:
#   ./run_vllm_e2e.sh [NPU_DEVICE_ID]
#
# 需要: xxhash (pip install xxhash)
# ============================================================================

set -euo pipefail

NPU_DEVICE="${1:-5}"
GRPC_PORT=50055
VLLM_PORT=8100
TAG="vllm-e2e-$(date +%H%M%S)"
SERVER_LOG="/tmp/pf-server-${TAG}.log"
VLLM_LOG="/tmp/vllm-server-${TAG}.log"
MODEL="/root/.cache/modelscope/models/qwen--Qwen2.5-0.5B-Instruct/snapshots/master"

export LD_LIBRARY_PATH="\
/root/miniconda3/envs/vllm-hust-dev/lib:\
/usr/local/Ascend/cann-8.5.1/aarch64-linux/lib64:\
/usr/local/Ascend/driver/lib64/driver:\
/usr/local/Ascend/nnal/atb/8.5.1/atb/cxx_abi_1/lib"
export ASCEND_VISIBLE_DEVICES="${NPU_DEVICE}"
export VLLM_PLUGINS=ascend
PYTHON="/root/miniconda3/envs/vllm-hust-dev/bin/python"
CARGO_TARGET="/workspace/pegaflow-hust/target/debug"

echo "============================================================"
echo " PegaFlow + vLLM E2E Integration Test"
echo " NPU: ${NPU_DEVICE}  gRPC: ${GRPC_PORT}  vLLM: ${VLLM_PORT}"
echo " Model: Qwen2.5-0.5B-Instruct"
echo " Tag: ${TAG}"
echo "============================================================"

# ---- Cleanup ----
echo "[0/5] Cleaning up stale processes..."
kill $(ps aux | grep "pegaflow-server-py" | grep -v grep | awk '{print $2}') 2>/dev/null || true
kill $(ps aux | grep "vllm.entrypoints" | grep -v grep | awk '{print $2}') 2>/dev/null || true
sleep 2

# ---- Build ----
echo "[1/5] Building pegaflow..."
cd /workspace/pegaflow-hust
PYO3_PYTHON="${PYTHON}" cargo build --no-default-features --features ascend \
  -p pegaflow-py --bin pegaflow-server-py 2>&1 | tail -1
cp -f "${CARGO_TARGET}/libpegaflow.so" \
  /workspace/pegaflow-hust/python/pegaflow/pegaflow.cpython-311-aarch64-linux-gnu.so
echo "  Build OK"

# ---- Start pegaflow-server ----
echo "[2/5] Starting pegaflow-server..."
nohup "${CARGO_TARGET}/pegaflow-server-py" \
  --addr "127.0.0.1:${GRPC_PORT}" \
  --devices "${NPU_DEVICE}" \
  --pool-size 2gb \
  --disable-numa-affinity \
  > "${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:9091/health >/dev/null 2>&1; then
    echo "  Server ready (${i}s)"
    break
  fi
  if ! kill -0 ${SERVER_PID} 2>/dev/null; then
    echo "  FAIL: Server crashed."; tail -20 "${SERVER_LOG}"; exit 1
  fi
  sleep 1
done

# ---- Start vLLM ----
echo "[3/5] Starting vLLM API server (model loading takes 30-90s)..."
nohup "${PYTHON}" -m vllm.entrypoints.openai.api_server \
  --model "${MODEL}" \
  --port "${VLLM_PORT}" \
  --max-model-len 1024 \
  --gpu-memory-utilization 0.1 \
  --enforce-eager \
  --kv-transfer-config '{"kv_connector":"PegaKVConnector","kv_role":"kv_both","kv_connector_module_path":"pegaflow.connector"}' \
  > "${VLLM_LOG}" 2>&1 &
VLLM_PID=$!

for i in $(seq 1 180); do
  if curl -sf "http://127.0.0.1:${VLLM_PORT}/health" >/dev/null 2>&1; then
    echo "  vLLM ready (${i}s)"
    break
  fi
  if ! kill -0 ${VLLM_PID} 2>/dev/null; then
    echo "  FAIL: vLLM crashed."
    grep -E "error|Error|panic|PegaKV|connect" "${VLLM_LOG}" | tail -10
    kill ${SERVER_PID} 2>/dev/null || true
    exit 1
  fi
  sleep 3
done

# ---- Send requests ----
echo "[4/5] Sending requests..."
LONG_PROMPT="Write a comprehensive essay about artificial intelligence. Cover the history from the 1950s to the present, major machine learning paradigms including supervised unsupervised and reinforcement learning, deep learning architectures like CNNs RNNs and Transformers, large language models, and ethical considerations. Provide detailed technical explanations and specific examples for each topic area discussed."

for i in 1 2 3; do
  echo -n "  Request ${i}: "
  t0=$(date +%s%N)
  RESP=$("${PYTHON}" -c "
import urllib.request, json, time
data = json.dumps({
    'model': '${MODEL}',
    'messages': [{'role': 'user', 'content': '${LONG_PROMPT}'}],
    'max_tokens': 64
}).encode()
req = urllib.request.Request('http://127.0.0.1:${VLLM_PORT}/v1/chat/completions',
    data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=120)
d = json.loads(resp.read())
if 'error' in d: print(f'ERROR: {d[\"error\"]}')
else: print(f'OK tokens={d[\"usage\"][\"prompt_tokens\"]}/{d[\"usage\"][\"completion_tokens\"]}')
" 2>&1)
  echo "${RESP}"
  sleep 3
done

# ---- Check metrics ----
echo "[5/5] Checking PegaFlow metrics..."
"${PYTHON}" -c "
import urllib.request
resp = urllib.request.urlopen('http://127.0.0.1:9091/metrics')
lines = resp.read().decode().split('\n')
for l in lines:
    l = l.strip()
    if 'rpc_requests_total{method=\"register\"' in l and 'ok' in l: print(f'  REG:   {l}')
    if 'rpc_requests_total{method=\"save\"' in l and 'ok' in l: print(f'  SAVE:  {l}')
    if 'save_bytes_total' in l and not l.startswith('#'): print(f'  BYTES: {l}')
    if 'save_duration_seconds_count' in l and not l.startswith('#'): print(f'  OPS:   {l}')
"

# ---- Cleanup ----
echo ""
echo "Stopping services..."
kill ${VLLM_PID} 2>/dev/null || true
kill ${SERVER_PID} 2>/dev/null || true
sleep 2

echo ""
echo "============================================================"
echo " vLLM + PegaFlow E2E Test Complete"
echo " Tag: ${TAG}"
echo " Logs: ${SERVER_LOG} / ${VLLM_LOG}"
echo "============================================================"
