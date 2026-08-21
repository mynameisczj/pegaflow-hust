# T2: concurrency=4 interval=200ms Summary

## Environment
- Commit: `cded3a2a1ffd` (parent: `f76003dace00`)
- Branch: `feature/trace-audit-extension`
- Runtime vLLM commit: `43341b177dba`
- Runtime ascend commit: `0a46364814ee`
- Torch/torch_npu: `2.10.0+cpu 2.10.0`
- Model: `Qwen3-8B` (md5: `85a491bc89ba`)
- Timestamp: 2026-08-18T14:24:43+0000
- NPUs: 8× Ascend 910B2 (see artifact for full npu-smi)

## TTFT (Time-To-First-Token)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **0.1550** | 0.2072 | 0.1968 | [0.1684, 0.2528] | 0.0951 | 0.3925 |
| Isolated | 48 | **0.1568** | 0.3834 | 0.7852 | [0.2855, 0.4820] | 0.1455 | 0.9491 |

## Total latency (full response)

| Phase | N | Median | Mean | IQR | 95% CI | Min | Max |
|---|---|---|---|---|---|---|---|
| Shared | 24 | **1.2795** | 1.3315 | 0.1982 | [1.2924, 1.3781] | 1.2102 | 1.5172 |
| Isolated | 48 | **1.2851** | 1.5089 | 0.7888 | [1.4111, 1.6081] | 1.2644 | 2.0813 |

## Per-Query Paired Analysis

### Q-1
- No paired observations (arm aborted by fail-close).
- Verdict: BREAK-EVEN (no data)

### Q0
- Shared: n=8, median=0.3761s
- Isolated: n=16, median=0.9398s
- Prefill saved (median): +563.7ms
- DMA cost (per-request, bound): 128.5ms
- Per-instance median paired delta (D5): NPU0:+601.2ms, NPU1:+565.9ms, NPU2:+592.1ms, NPU3:+584.2ms, NPU4:+568.2ms, NPU5:+786.3ms, NPU6:-228.7ms, NPU7:+547.1ms
- Lifecycle cluster CI, per query class (C5): CI [502.0, 502.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved > dma_cost AND significant -> **GO**

### Q1
- Shared: n=8, median=0.1529s
- Isolated: n=16, median=0.1525s
- Prefill saved (median): -0.4ms
- DMA cost (per-request, bound): n/a (no DMA evidence)
- Per-instance median paired delta (D5): NPU0:-6.1ms, NPU1:-0.9ms, NPU2:+8.0ms, NPU3:+3.2ms, NPU4:-4.6ms, NPU5:-8.3ms, NPU6:-4.2ms, NPU7:-4.5ms
- Lifecycle cluster CI, per query class (C5): CI [-2.2, -2.2]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

### Q2
- Shared: n=8, median=0.1550s
- Isolated: n=16, median=0.1566s
- Prefill saved (median): +1.6ms
- DMA cost (per-request, bound): 1.8ms
- Per-instance median paired delta (D5): NPU0:+53.7ms, NPU1:+0.3ms, NPU2:-8.2ms, NPU3:+3.7ms, NPU4:+54.8ms, NPU5:-4.3ms, NPU6:+56.9ms, NPU7:+59.0ms
- Lifecycle cluster CI, per query class (C5): CI [27.0, 27.0]ms excludes 0
- Break-even (prereg §4.4): prefill_saved <= dma_cost OR not significant -> **BREAK-EVEN**

## Negative Examples (Preserved)

### burst_concurrent_8inst
- Shared avg TTFT: 2.7s
- Isolated avg TTFT: 1.73s
- Result: +56% (shared WORSE)
- Root cause: 8 concurrent DMA streams saturate PCIe uplink
- Verdict: Burst is unrealistic workload; staggered/normal serving load unaffected

### mla_tp8_deepseek_v2_lite
- Shared avg TTFT: 0.184s
- Isolated avg TTFT: 0.187s
- Result: +1.6% (no meaningful gain)
- Root cause: MLA kv_lora_rank=512 compresses KV compute to ~100ms; DMA of compressed KV ~3ms
- Verdict: PegaFlow requires large enough prefill gap to overcome DMA cost

## Producer (Warmup Seed) Records
- Count: 3
- Median TTFT: 0.9345s
- Excluded from consumer paired-delta analysis.

## Evidence Violations (Fail-Close)

- [INVALID] duplicate connector event: req= keys=['cmpl-perf-2c1fbb922dea-0-9ce5efa0', 'cmpl-perf-ed8388ab2920-0-a92e3d54', 'cmpl-perf-c3f3e1f21c81-0-b4069d9b', 'cmpl-perf-a70840dccd54-0-84a18513', 'cmpl-perf-41d9657302b9-0-b62c324d', 'cmpl-perf-e56c43f3078f-0-ae312022', 'cmpl-perf-cda96d6a1ef0-0-84de8570', 'cmpl-perf-bce93a94ce7a-0-945453a5', 'cmpl-perf-1aac7746547e-0-80d20499', 'cmpl-perf-d4800d3d5d0d-0-9f37ccb4', 'cmpl-perf-8c97c934c087-0-885f0b1e', 'cmpl-perf-9ee2d45cd1a8-0-8ef2245b', 'cmpl-perf-1f32bd6ec4ab-0-9600fcca', 'cmpl-perf-6e7c43b3fcd8-0-b69c0f69', 'cmpl-perf-95fdbaa84264-0-943107e3', 'cmpl-perf-5c25d21075f0-0-80ea3d77', 'cmpl-perf-f291569c4f24-0-bceef80a', 'cmpl-perf-2f77eb6455a5-0-bdf45a4b', 'cmpl-perf-30115dbc70ba-0-aa5afbcc', 'cmpl-perf-0fce80cbef9c-0-b9a4391b', 'cmpl-perf-6b23d10a29b6-0-a6ac760b', 'cmpl-perf-31e3afc2a568-0-b8dc0fc1', 'cmpl-perf-5548979b4dec-0-a1c31b7c', 'cmpl-perf-b1e1f88a27e9-0-ba588f03', 'cmpl-perf-77ffd01f9dad-0-ab59c5d8', 'cmpl-perf-b4a4dbb22bfa-0-96a96996', 'cmpl-perf-b5f2032c831f-0-9c9d6f88', 'cmpl-perf-686b2c9a0679-0-a6cf87b6', 'cmpl-perf-426e8a2a99b6-0-a1571053', 'cmpl-perf-f7c31ebba8e9-0-92b2d3ec', 'cmpl-perf-6aa07a2b5cab-0-ba677824', 'cmpl-perf-356de0dff38c-0-baccc006', 'cmpl-perf-441dbed8d169-0-ae2eae57', 'cmpl-perf-d4fbb7e3e551-0-bbcededf', 'cmpl-perf-e80684b5ccde-0-ac0dcaac', 'cmpl-perf-402541affe8b-0-9417f2d8', 'cmpl-perf-b08d5987acc0-0-a7a27446', 'cmpl-perf-bd2e127ddd4c-0-9f572d47', 'cmpl-perf-edc786b1dae7-0-8bf2d59d', 'cmpl-perf-7757c7776d5a-0-9a9fbb14', 'cmpl-perf-599f7db6b4ba-0-8ada759b', 'cmpl-perf-ff4457cf1175-0-a6104d6d', 'cmpl-perf-e2a5117c84c3-0-8b4e06e8', 'cmpl-perf-0c0dd684f8c7-0-abec7f57', 'cmpl-perf-d9a7b069d5ee-0-bc35356c', 'cmpl-perf-80a0352fb48a-0-a8f894ac', 'cmpl-perf-9a426470e58c-0-af65f5cc', 'cmpl-perf-701e7460c940-0-bdc7d175', 'cmpl-perf-f3844203c1b0-0-bf392dfb', 'cmpl-perf-9fb974665684-0-a26ab2c8', 'cmpl-perf-9394ff0d5530-0-a3cac69e', 'cmpl-perf-fac992ceee9f-0-a1b602ac', 'cmpl-perf-dceafffae2db-0-844e10e3', 'cmpl-perf-3282baad5069-0-befc23bd', 'cmpl-perf-87fbeb5d6178-0-a9bad901', 'cmpl-perf-ca059d36e923-0-98235eaf', 'cmpl-perf-075fb5271c3b-0-ab34b671', 'cmpl-perf-c3ca425413fd-0-a3221290', 'cmpl-perf-de24a08fb955-0-a66fd525', 'cmpl-perf-a9686153d3e4-0-86778f3c', 'cmpl-perf-3ec62e4a6a66-0-aac3d203', 'cmpl-perf-a1fe6a2afc28-0-9fa8b504', 'cmpl-perf-ad2c6a352d19-0-88aae841', 'cmpl-perf-5fefb4b1ace8-0-89fafde3', 'cmpl-perf-c04757df48aa-0-88420145', 'cmpl-perf-6cdbd159a943-0-a39194e6', 'cmpl-perf-66d44804bf3f-0-806c5e3a', 'cmpl-perf-07deef8f9890-0-a3218d3f', 'cmpl-perf-6524a06ad45b-0-a87d1377', 'cmpl-perf-eb392f71181c-0-9455bcd6', 'cmpl-perf-a6998ce77c16-0-89a2020e', 'cmpl-perf-f104ce8cf157-0-8098bd4e', 'cmpl-perf-41eb6c084497-0-a76502bd', 'cmpl-perf-ea7410d23202-0-a91afedd', 'cmpl-perf-de229503bd9e-0-a6e3caf4']
- [INVALID] duplicate connector event: req= keys=['cmpl-perf-2c1fbb922dea-0-9ce5efa0', 'cmpl-perf-ed8388ab2920-0-a92e3d54', 'cmpl-perf-c3f3e1f21c81-0-b4069d9b', 'cmpl-perf-a70840dccd54-0-84a18513', 'cmpl-perf-41d9657302b9-0-b62c324d', 'cmpl-perf-e56c43f3078f-0-ae312022', 'cmpl-perf-cda96d6a1ef0-0-84de8570', 'cmpl-perf-bce93a94ce7a-0-945453a5', 'cmpl-perf-1aac7746547e-0-80d20499', 'cmpl-perf-d4800d3d5d0d-0-9f37ccb4', 'cmpl-perf-8c97c934c087-0-885f0b1e', 'cmpl-perf-9ee2d45cd1a8-0-8ef2245b', 'cmpl-perf-1f32bd6ec4ab-0-9600fcca', 'cmpl-perf-6e7c43b3fcd8-0-b69c0f69', 'cmpl-perf-95fdbaa84264-0-943107e3', 'cmpl-perf-5c25d21075f0-0-80ea3d77', 'cmpl-perf-f291569c4f24-0-bceef80a', 'cmpl-perf-2f77eb6455a5-0-bdf45a4b', 'cmpl-perf-30115dbc70ba-0-aa5afbcc', 'cmpl-perf-0fce80cbef9c-0-b9a4391b', 'cmpl-perf-6b23d10a29b6-0-a6ac760b', 'cmpl-perf-31e3afc2a568-0-b8dc0fc1', 'cmpl-perf-5548979b4dec-0-a1c31b7c', 'cmpl-perf-b1e1f88a27e9-0-ba588f03', 'cmpl-perf-77ffd01f9dad-0-ab59c5d8', 'cmpl-perf-b4a4dbb22bfa-0-96a96996', 'cmpl-perf-b5f2032c831f-0-9c9d6f88', 'cmpl-perf-686b2c9a0679-0-a6cf87b6', 'cmpl-perf-426e8a2a99b6-0-a1571053', 'cmpl-perf-f7c31ebba8e9-0-92b2d3ec', 'cmpl-perf-6aa07a2b5cab-0-ba677824', 'cmpl-perf-356de0dff38c-0-baccc006', 'cmpl-perf-441dbed8d169-0-ae2eae57', 'cmpl-perf-d4fbb7e3e551-0-bbcededf', 'cmpl-perf-e80684b5ccde-0-ac0dcaac', 'cmpl-perf-402541affe8b-0-9417f2d8', 'cmpl-perf-b08d5987acc0-0-a7a27446', 'cmpl-perf-bd2e127ddd4c-0-9f572d47', 'cmpl-perf-edc786b1dae7-0-8bf2d59d', 'cmpl-perf-7757c7776d5a-0-9a9fbb14', 'cmpl-perf-599f7db6b4ba-0-8ada759b', 'cmpl-perf-ff4457cf1175-0-a6104d6d', 'cmpl-perf-e2a5117c84c3-0-8b4e06e8', 'cmpl-perf-0c0dd684f8c7-0-abec7f57', 'cmpl-perf-d9a7b069d5ee-0-bc35356c', 'cmpl-perf-80a0352fb48a-0-a8f894ac', 'cmpl-perf-9a426470e58c-0-af65f5cc', 'cmpl-perf-701e7460c940-0-bdc7d175', 'cmpl-perf-f3844203c1b0-0-bf392dfb', 'cmpl-perf-9fb974665684-0-a26ab2c8', 'cmpl-perf-9394ff0d5530-0-a3cac69e', 'cmpl-perf-fac992ceee9f-0-a1b602ac', 'cmpl-perf-dceafffae2db-0-844e10e3', 'cmpl-perf-3282baad5069-0-befc23bd', 'cmpl-perf-87fbeb5d6178-0-a9bad901', 'cmpl-perf-ca059d36e923-0-98235eaf', 'cmpl-perf-075fb5271c3b-0-ab34b671', 'cmpl-perf-c3ca425413fd-0-a3221290', 'cmpl-perf-de24a08fb955-0-a66fd525', 'cmpl-perf-a9686153d3e4-0-86778f3c', 'cmpl-perf-3ec62e4a6a66-0-aac3d203', 'cmpl-perf-a1fe6a2afc28-0-9fa8b504', 'cmpl-perf-ad2c6a352d19-0-88aae841', 'cmpl-perf-5fefb4b1ace8-0-89fafde3', 'cmpl-perf-c04757df48aa-0-88420145', 'cmpl-perf-6cdbd159a943-0-a39194e6', 'cmpl-perf-66d44804bf3f-0-806c5e3a', 'cmpl-perf-07deef8f9890-0-a3218d3f', 'cmpl-perf-6524a06ad45b-0-a87d1377', 'cmpl-perf-eb392f71181c-0-9455bcd6', 'cmpl-perf-a6998ce77c16-0-89a2020e', 'cmpl-perf-f104ce8cf157-0-8098bd4e', 'cmpl-perf-41eb6c084497-0-a76502bd', 'cmpl-perf-ea7410d23202-0-a91afedd', 'cmpl-perf-de229503bd9e-0-a6e3caf4']
- [INVALID] duplicate connector event: req= keys=['cmpl-perf-2c1fbb922dea-0-9ce5efa0', 'cmpl-perf-ed8388ab2920-0-a92e3d54', 'cmpl-perf-c3f3e1f21c81-0-b4069d9b', 'cmpl-perf-a70840dccd54-0-84a18513', 'cmpl-perf-41d9657302b9-0-b62c324d', 'cmpl-perf-e56c43f3078f-0-ae312022', 'cmpl-perf-cda96d6a1ef0-0-84de8570', 'cmpl-perf-bce93a94ce7a-0-945453a5', 'cmpl-perf-1aac7746547e-0-80d20499', 'cmpl-perf-d4800d3d5d0d-0-9f37ccb4', 'cmpl-perf-8c97c934c087-0-885f0b1e', 'cmpl-perf-9ee2d45cd1a8-0-8ef2245b', 'cmpl-perf-1f32bd6ec4ab-0-9600fcca', 'cmpl-perf-6e7c43b3fcd8-0-b69c0f69', 'cmpl-perf-95fdbaa84264-0-943107e3', 'cmpl-perf-5c25d21075f0-0-80ea3d77', 'cmpl-perf-f291569c4f24-0-bceef80a', 'cmpl-perf-2f77eb6455a5-0-bdf45a4b', 'cmpl-perf-30115dbc70ba-0-aa5afbcc', 'cmpl-perf-0fce80cbef9c-0-b9a4391b', 'cmpl-perf-6b23d10a29b6-0-a6ac760b', 'cmpl-perf-31e3afc2a568-0-b8dc0fc1', 'cmpl-perf-5548979b4dec-0-a1c31b7c', 'cmpl-perf-b1e1f88a27e9-0-ba588f03', 'cmpl-perf-77ffd01f9dad-0-ab59c5d8', 'cmpl-perf-b4a4dbb22bfa-0-96a96996', 'cmpl-perf-b5f2032c831f-0-9c9d6f88', 'cmpl-perf-686b2c9a0679-0-a6cf87b6', 'cmpl-perf-426e8a2a99b6-0-a1571053', 'cmpl-perf-f7c31ebba8e9-0-92b2d3ec', 'cmpl-perf-6aa07a2b5cab-0-ba677824', 'cmpl-perf-356de0dff38c-0-baccc006', 'cmpl-perf-441dbed8d169-0-ae2eae57', 'cmpl-perf-d4fbb7e3e551-0-bbcededf', 'cmpl-perf-e80684b5ccde-0-ac0dcaac', 'cmpl-perf-402541affe8b-0-9417f2d8', 'cmpl-perf-b08d5987acc0-0-a7a27446', 'cmpl-perf-bd2e127ddd4c-0-9f572d47', 'cmpl-perf-edc786b1dae7-0-8bf2d59d', 'cmpl-perf-7757c7776d5a-0-9a9fbb14', 'cmpl-perf-599f7db6b4ba-0-8ada759b', 'cmpl-perf-ff4457cf1175-0-a6104d6d', 'cmpl-perf-e2a5117c84c3-0-8b4e06e8', 'cmpl-perf-0c0dd684f8c7-0-abec7f57', 'cmpl-perf-d9a7b069d5ee-0-bc35356c', 'cmpl-perf-80a0352fb48a-0-a8f894ac', 'cmpl-perf-9a426470e58c-0-af65f5cc', 'cmpl-perf-701e7460c940-0-bdc7d175', 'cmpl-perf-f3844203c1b0-0-bf392dfb', 'cmpl-perf-9fb974665684-0-a26ab2c8', 'cmpl-perf-9394ff0d5530-0-a3cac69e', 'cmpl-perf-fac992ceee9f-0-a1b602ac', 'cmpl-perf-dceafffae2db-0-844e10e3', 'cmpl-perf-3282baad5069-0-befc23bd', 'cmpl-perf-87fbeb5d6178-0-a9bad901', 'cmpl-perf-ca059d36e923-0-98235eaf', 'cmpl-perf-075fb5271c3b-0-ab34b671', 'cmpl-perf-c3ca425413fd-0-a3221290', 'cmpl-perf-de24a08fb955-0-a66fd525', 'cmpl-perf-a9686153d3e4-0-86778f3c', 'cmpl-perf-3ec62e4a6a66-0-aac3d203', 'cmpl-perf-a1fe6a2afc28-0-9fa8b504', 'cmpl-perf-ad2c6a352d19-0-88aae841', 'cmpl-perf-5fefb4b1ace8-0-89fafde3', 'cmpl-perf-c04757df48aa-0-88420145', 'cmpl-perf-6cdbd159a943-0-a39194e6', 'cmpl-perf-66d44804bf3f-0-806c5e3a', 'cmpl-perf-07deef8f9890-0-a3218d3f', 'cmpl-perf-6524a06ad45b-0-a87d1377', 'cmpl-perf-eb392f71181c-0-9455bcd6', 'cmpl-perf-a6998ce77c16-0-89a2020e', 'cmpl-perf-f104ce8cf157-0-8098bd4e', 'cmpl-perf-41eb6c084497-0-a76502bd', 'cmpl-perf-ea7410d23202-0-a91afedd', 'cmpl-perf-de229503bd9e-0-a6e3caf4']

## Validity Manifest
- Run ID: 20260818-142432
- Total records: 78
- Consumer shared records: 24
- Consumer isolated records: 48
- Producer records: 3
- INVALID records: 3
- Audit-invalid records (evidence): 3
- Conservation: BROKEN (connector dup=222, orphans=0/0/0, leftover DMA=0, fallback DMA (bound)=0)
- Validity gate: FAIL
- Audit verdict: INVALID

## Reproduce
- Command: `python scripts/run_perf_t2-c4-i200_baseline.py --cycles 3 --requests-per-phase 3 --pool-size 16gb --num-instances 8`

