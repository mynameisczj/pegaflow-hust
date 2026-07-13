#!/usr/bin/env python3
"""P2-2: Multi-layer (K+V) E2E Save/Load test."""
import hashlib, os, pickle, socket, subprocess, sys, time
import torch
from pegaflow.npu_ipc_wrapper import NpuIPCWrapper
from pegaflow.pegaflow import EngineRpcClient, PyLoadState

def test_e2e():
    print("=" * 60)
    print("PegaFlow Ascend E2E — K+V Dual-Layer Save/Load")
    print("=" * 60)

    port = 50061
    subprocess.run(["pkill", "-f", f"pegaflow-server-py.*{port}"], capture_output=True)
    time.sleep(1)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/root/miniconda3/envs/vllm-hust-dev/lib:/usr/local/Ascend/cann-8.5.1/aarch64-linux/lib64:/usr/local/Ascend/driver/lib64/driver"
    server = subprocess.Popen(
        ["/workspace/pegaflow-hust/target/debug/pegaflow-server-py",
         "--addr", f"127.0.0.1:{port}", "--devices", "4",
         "--pool-size", "500mb", "--disable-numa-affinity"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    print("[1/5] Server...", end="", flush=True)
    deadline = time.perf_counter() + 60
    while time.perf_counter() < deadline:
        if server.poll() is not None: print(" FAIL"); return False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", port)) == 0: s.close(); break
        s.close(); time.sleep(0.5); print(".", end="", flush=True)
    print(f" ready")

    try:
        dev, N, T, H, D = "npu:4", 8, 128, 8, 128
        BS = T * H * D * 2
        client = EngineRpcClient(f"http://127.0.0.1:{port}")

        print("[2/5] K+V tensors + register...")
        k = torch.empty(N, T, H, D, dtype=torch.float16, device=dev); k.normal_()
        v = torch.empty(N, T, H, D, dtype=torch.float16, device=dev); v.normal_()
        ko, vo = k.clone(), v.clone()
        kw, vw = NpuIPCWrapper(k), NpuIPCWrapper(v)
        print(f"  K: ptr={k.data_ptr():#x}  V: ptr={v.data_ptr():#x}")
        print(f"  IPC: K={'OK' if kw._handle else 'FAIL'}  V={'OK' if vw._handle else 'FAIL'}")

        ok, _ = client.register_context_batch(
            "e2e-multi", "e2e-ns", 0, 0, 1, 1, 4,
            ["k", "v"], [pickle.dumps(kw), pickle.dumps(vw)],
            [N, N], [BS, BS], [0, 0], [1, 1], "direct", False)
        print(f"  register: {'OK' if ok else 'FAIL'}")

        print("[3/5] Save...")
        S = 4
        torch.npu.synchronize(dev)
        # K and V share the same hash per block (they form one logical KV block)
        h = [hashlib.blake2b(
            k[i].contiguous().cpu().view(torch.uint8).numpy().tobytes() +
            v[i].contiguous().cpu().view(torch.uint8).numpy().tobytes(),
            digest_size=32).digest() for i in range(S)]
        kh, vh = h, h  # same hashes for same block
        t0 = time.perf_counter()
        ok, _ = client.save("e2e-multi", 0, 0, 4, [("k", list(range(S)), kh), ("v", list(range(S)), vh)])
        print(f"  save: {'OK' if ok else 'FAIL'}  {S*2*BS/1024:.0f}KB  {(time.perf_counter()-t0)*1000:.0f}ms")

        # Save is async — insert worker may take a moment. Retry a few times.
        print("[4/5] Query...")
        hit = 0
        for attempt in range(10):
            time.sleep(0.5)
            r = client.query_prefetch("e2e-multi", kh, f"e2e-{attempt}")
            hit = getattr(r, "num_hit_blocks", 0)
            if hit > 0:
                break
        print(f"  hit: {hit}/{S*2}")
        if hit > 0:
            k.zero_(); v.zero_(); torch.npu.synchronize(dev)
            ls = PyLoadState()
            t0 = time.perf_counter()
            ok, _ = client.load("e2e-multi", 0, 4, ls.shm_name(), ["k", "v"], [(r.lease, list(range(S)))])
            print(f"  load: {'OK' if ok else 'FAIL'}  {(time.perf_counter()-t0)*1000:.0f}ms")
            for _ in range(150):
                if ls.is_ready(): break
                time.sleep(0.2)
            print(f"  state: {ls.get_state()}")

            print("[5/5] Verify...")
            torch.npu.synchronize(dev)
            km = torch.allclose(k[:S], ko[:S]); vm = torch.allclose(v[:S], vo[:S])
            print(f"  K: {'MATCH' if km else 'MISMATCH'}  V: {'MATCH' if vm else 'MISMATCH'}")
            if km and vm:
                print(f"\n{'='*60}\n  E2E K+V: PASSED  |  Save/load: OK  |  Data: {S*2*BS/1024:.0f}KB\n{'='*60}")
                return True
        return False
    except Exception as e:
        print(f"\nFAIL: {e}"); import traceback; traceback.print_exc(); return False
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except subprocess.TimeoutExpired: server.kill()

if __name__ == "__main__":
    sys.exit(0 if test_e2e() else 1)
