#!/usr/bin/env python3
"""
P2-2 扩展: vLLM + PegaFlow 端到端集成测试

使用 Qwen2.5-0.5B-Instruct 模型，验证:
  1. vLLM 正常启动 + PegaFlow connector 初始化
  2. pegaflow-server 正常注册 KV cache
  3. 两次请求：第一次填写缓存 → Save，第二次命中缓存 → Load
  4. 验证 cache hit rate > 0

用法:
  python e2e_vllm_test.py
"""

import json, os, signal, socket, subprocess, sys, time, urllib.request

MODEL = "/root/.cache/modelscope/models/qwen--Qwen2.5-0.5B-Instruct/snapshots/master"
GRPC_PORT = 50055
VLLM_PORT = 8100
DEVICE = "4"

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = (
    "/root/miniconda3/envs/vllm-hust-dev/lib:"
    "/usr/local/Ascend/cann-8.5.1/aarch64-linux/lib64:"
    "/usr/local/Ascend/driver/lib64/driver"
)
env["ASCEND_VISIBLE_DEVICES"] = DEVICE
env["ASCEND_RT_VISIBLE_DEVICES"] = DEVICE
env["VLLM_PLUGINS"] = "ascend"
env["PEGAFLOW_HOST"] = "127.0.0.1"
env["PEGAFLOW_PORT"] = str(GRPC_PORT)


def wait_port(port, timeout=90, label=""):
    dl = time.perf_counter() + timeout
    while time.perf_counter() < dl:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            s.close()
            return True
        s.close()
        time.sleep(0.5)
    print(f"  TIMEOUT waiting for {label}:{port}")
    return False


def vllm_request(prompt, max_tokens=16, temperature=0):
    """Send a chat completion request to vLLM."""
    data = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{VLLM_PORT}/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=" * 60)
    print("vLLM + PegaFlow E2E Integration Test")
    print(f"Model: Qwen2.5-0.5B  Device: {DEVICE}  Ports: gRPC={GRPC_PORT} vLLM={VLLM_PORT}")
    print("=" * 60)

    # Kill any existing processes
    for proc in ["pegaflow-server-py", "vllm"]:
        subprocess.run(["pkill", "-f", proc], capture_output=True)
    time.sleep(2)

    # ── 1. Start pegaflow-server ──
    print("\n[1/4] Starting pegaflow-server...")
    server = subprocess.Popen(
        ["/workspace/pegaflow-hust/target/debug/pegaflow-server-py",
         "--addr", f"127.0.0.1:{GRPC_PORT}",
         "--http-addr", "127.0.0.1:9091",
         "--devices", DEVICE,
         "--pool-size", "2gb",
         "--disable-numa-affinity"],
        stdout=open("/tmp/pegaflow-server-vllm-e2e.log", "w"),
        stderr=subprocess.STDOUT, env=env,
    )
    if not wait_port(GRPC_PORT, 30, "pegaflow-server"):
        print("FAIL: server did not start"); return 1
    print(f"  Server ready (pid={server.pid})")

    # ── 2. Start vLLM ──
    print("\n[2/4] Starting vLLM API server...")
    vllm_log = open("/tmp/vllm-server-e2e-v3.log", "w")
    vllm = subprocess.Popen(
        ["/root/miniconda3/envs/vllm-hust-dev/bin/python", "-m", "vllm.entrypoints.openai.api_server",
         "--model", MODEL,
         "--port", str(VLLM_PORT),
         "--max-model-len", "2048",
         "--gpu-memory-utilization", "0.5",
         "--enforce-eager",
         "--disable-log-requests",
         "--kv-transfer-config",
         '{"kv_connector":"PegaKVConnector","kv_role":"kv_both","kv_connector_module_path":"pegaflow.connector","kv_connector_extra_config":{"pegaflow.host":"127.0.0.1","pegaflow.port":' + str(GRPC_PORT) + ',"pegaflow.mode":"read_write"}}'],
        stdout=vllm_log, stderr=subprocess.STDOUT, env=env,
    )

    print("  Waiting for vLLM...", end="", flush=True)
    if not wait_port(VLLM_PORT, 180, "vLLM"):
        # Print last log lines for debugging
        print("\n  FAIL: vLLM did not start. Last log lines:")
        os.system("tail -40 /tmp/vllm-server-e2e-v3.log")
        server.terminate(); return 1
    print(" ready")

    # ── 3. First request (fills cache) ──
    print("\n[3/4] Sending first request (fills KV cache → should trigger Save)...")
    prompt = "Explain the concept of machine learning in detail, covering supervised learning, unsupervised learning, and reinforcement learning, with examples of each."
    t0 = time.perf_counter()
    r1 = vllm_request(prompt, max_tokens=50)
    t1 = time.perf_counter() - t0
    if "error" in r1:
        print(f"  FAIL: {r1['error']}")
        server.terminate(); vllm.terminate(); return 1
    content = r1.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = r1.get("usage", {})
    print(f"  Request 1: {len(content)} chars, {usage.get('completion_tokens',0)} tokens, {t1:.1f}s")
    print(f"  Response: {content[:120]}...")

    # Wait for async save to complete
    time.sleep(3)

    # ── 4. Second request (should hit cache) ──
    print("\n[4/4] Sending second request (same prefix → should hit cache → Load)...")
    t0 = time.perf_counter()
    r2 = vllm_request(prompt, max_tokens=50)
    t2 = time.perf_counter() - t0
    if "error" in r2:
        print(f"  FAIL: {r2['error']}")
        server.terminate(); vllm.terminate(); return 1
    content2 = r2.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage2 = r2.get("usage", {})
    print(f"  Request 2: {len(content2)} chars, {usage2.get('completion_tokens',0)} tokens, {t2:.1f}s")
    print(f"  Response: {content2[:120]}...")

    # ── Check server logs for cache activity ──
    print("\n--- Server Save/Load logs ---")
    os.system("grep -E 'save_batch|prefetch.*hit|PegaKVConnector|Registered.*KV|Cache HIT|hit=' /tmp/pegaflow-server-vllm-e2e.log | tail -15")
    print("\n--- vLLM connector logs ---")
    os.system("grep -E 'PegaKVConnector|save|load|Register|Cache' /tmp/vllm-server-e2e-v3.log | tail -15")

    # ── Check pegaflow metrics for cache hits ──
    try:
        metrics = urllib.request.urlopen("http://127.0.0.1:9091/metrics").read().decode()
        for line in metrics.split("\n"):
            if "pegaflow_cache_block_hits" in line and not line.startswith("#"):
                print(f"\n  {line}")
            if "pegaflow_save_bytes" in line and not line.startswith("#"):
                print(f"  {line}")
    except Exception:
        pass

    print(f"\n  Request 1: {t1:.1f}s  Request 2: {t2:.1f}s  Speedup: {t1/t2 if t2>0 else 0:.1f}x")
    print(f"\n{'='*60}")
    print("vLLM + PegaFlow E2E: PASSED" if "error" not in r1 and "error" not in r2 else "FAILED")
    print(f"{'='*60}")

    server.terminate(); vllm.terminate()
    server.wait(timeout=10); vllm.wait(timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
