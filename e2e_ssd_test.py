#!/usr/bin/env python3
"""P2-4: SSD Cache E2E test — verify save→SSD→evict→load_from_SSD pipeline"""
import hashlib, os, pickle, shutil, socket, subprocess, sys, time
import torch
from pegaflow.npu_ipc_wrapper import NpuIPCWrapper
from pegaflow.pegaflow import EngineRpcClient, PyLoadState

SSD_PATH = "/tmp/ssd_e2e_test"
PORT = 50063

def test_ssd():
    print("=" * 60)
    print("PegaFlow Ascend E2E — SSD Cache Save/Load")
    print("=" * 60)

    # Clean SSD directory
    shutil.rmtree(SSD_PATH, ignore_errors=True)
    os.makedirs(SSD_PATH, exist_ok=True)

    subprocess.run(["pkill", "-f", f"pegaflow-server-py.*{PORT}"], capture_output=True)
    time.sleep(1)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/root/miniconda3/envs/vllm-hust-dev/lib:/usr/local/Ascend/cann-8.5.1/aarch64-linux/lib64:/usr/local/Ascend/driver/lib64/driver"

    server = subprocess.Popen(
        ["/workspace/pegaflow-hust/target/debug/pegaflow-server-py",
         "--addr", f"127.0.0.1:{PORT}", "--devices", "4",
         "--pool-size", "500mb", "--disable-numa-affinity",
         "--ssd-cache-path", SSD_PATH,
         "--ssd-cache-capacity", "1gb"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

    print("[1/6] Server + SSD...", end="", flush=True)
    dl = time.perf_counter() + 90
    while time.perf_counter() < dl:
        if server.poll() is not None: print(" FAIL"); return False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", PORT)) == 0: s.close(); break
        s.close(); time.sleep(0.5); print(".", end="", flush=True)
    print(" ready")

    try:
        dev, N, T, H, D = "npu:4", 8, 128, 8, 128
        BS = T * H * D * 2
        client = EngineRpcClient(f"http://127.0.0.1:{PORT}")

        print("[2/6] Register context...")
        k = torch.empty(N, T, H, D, dtype=torch.float16, device=dev); k.normal_()
        v = torch.empty(N, T, H, D, dtype=torch.float16, device=dev); v.normal_()
        ko, vo = k.clone(), v.clone()
        kw, vw = NpuIPCWrapper(k), NpuIPCWrapper(v)
        ok, _ = client.register_context_batch(
            "ssd-test", "ssd-ns", 0, 0, 1, 1, 4,
            ["k", "v"], [pickle.dumps(kw), pickle.dumps(vw)],
            [N, N], [BS, BS], [0, 0], [1, 1], "direct", False)
        print(f"  register: {'OK' if ok else 'FAIL'}")

        S = 4
        torch.npu.synchronize(dev)
        h = [hashlib.blake2b(
            k[i].contiguous().cpu().view(torch.uint8).numpy().tobytes() +
            v[i].contiguous().cpu().view(torch.uint8).numpy().tobytes(),
            digest_size=32).digest() for i in range(S)]

        print("[3/6] Save (D2H → SSD)...")
        t0 = time.perf_counter()
        ok, _ = client.save("ssd-test", 0, 0, 4,
                            [("k", list(range(S)), h), ("v", list(range(S)), h)])
        print(f"  save: {'OK' if ok else 'FAIL'}  {(time.perf_counter()-t0)*1000:.0f}ms")

        # Wait for SSD write to complete (flush pipeline)
        time.sleep(2)

        # Check SSD files exist
        ssd_files = list(os.listdir(SSD_PATH))
        print(f"  SSD files: {len(ssd_files)} ({', '.join(ssd_files[:3])}...)")
        ssd_size = sum(os.path.getsize(os.path.join(SSD_PATH, f)) for f in ssd_files)
        print(f"  SSD total size: {ssd_size/1024:.0f}KB")

        print("[4/6] Evict from RAM cache...")
        # Query to get lease, then evict
        r = client.query_prefetch("ssd-test", h, "prefetch")
        hit = getattr(r, "num_hit_blocks", 0)
        print(f"  RAM hit: {hit}")
        if hit > 0:
            client.release(r.lease)

        # Cleanup memory cache (forces eviction of all blocks)
        import urllib.request
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:9091/cache/memory/cleanup")
            print(f"  memory cleanup: {resp.status}")
        except Exception as e:
            print(f"  cleanup via HTTP: {e}")

        time.sleep(1)

        print("[5/6] Query (SSD-backed prefetch)...")
        r = client.query_prefetch("ssd-test", h, "after-evict")
        hit2 = getattr(r, "num_hit_blocks", 0)
        print(f"  after eviction hit: {hit2}")

        if hit2 > 0:
            k.zero_(); v.zero_(); torch.npu.synchronize(dev)
            ls = PyLoadState()
            t0 = time.perf_counter()
            ok, _ = client.load("ssd-test", 0, 4, ls.shm_name(), ["k", "v"],
                                [(r.lease, list(range(S)))])
            print(f"  load: {'OK' if ok else 'FAIL'}  {(time.perf_counter()-t0)*1000:.0f}ms")
            for _ in range(300):  # SSD read may take longer
                if ls.is_ready(): break
                time.sleep(0.2)
            state = ls.get_state()
            print(f"  load state: {state}")

            print("[6/6] Verify...")
            torch.npu.synchronize(dev)
            km = torch.allclose(k[:S], ko[:S])
            vm = torch.allclose(v[:S], vo[:S])
            print(f"  K: {'MATCH' if km else 'MISMATCH'}  V: {'MATCH' if vm else 'MISMATCH'}")
            if km and vm:
                print(f"\n{'='*60}\n  SSD E2E: PASSED  |  RAM→SSD→RAM  |  Data: {S*2*BS/1024:.0f}KB\n{'='*60}")
                return True
        else:
            print("  FAIL: blocks not found after eviction (SSD prefetch may have failed)")
        return False
    except Exception as e:
        print(f"\nFAIL: {e}"); import traceback; traceback.print_exc(); return False
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except subprocess.TimeoutExpired: server.kill()
        shutil.rmtree(SSD_PATH, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(0 if test_ssd() else 1)
