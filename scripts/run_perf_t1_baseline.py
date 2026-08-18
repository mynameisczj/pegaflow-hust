#!/usr/bin/env python3
"""
run_perf_t1_baseline.py — T1: baseline matched evaluation.

Qwen3-8B, 8 instances, 3 cycles, AB/BA alternation. Adds TBT/TPOT metrics
to the validated trace-audit methodology. Cross-checkable against the
20260813 VALID artifact (results/trace-audit/20260813-090821/).

Preregistered (perf plan §T1):
  - break-even gate: prefill_saved > dma_cost AND cluster CI excludes 0
  - TBT stability: shared TBT p95 must not degrade > 10% vs isolated
    (decode-path regression check, informational gate)

Usage:
  python scripts/run_perf_t1_baseline.py [--cycles 3] [--requests-per-phase 3]
      [--pool-size 16gb] [--num-instances 8] [--dry-run] [--verify-repro]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_perf_base import Experiment, run_experiment


def _tbt_gate(all_records, merge_result) -> list[str]:
    """TBT stability gate: shared p95 must not exceed isolated p95 * 1.10.

    TBT = per-token decode latency. A shared-arm regression would show up
    here (e.g. DMA contention stealing decode bandwidth).
    """
    shared = [r for r in all_records
              if r.get("phase") == "shared" and r.get("ok")
              and r.get("tbt_p95_s", -1) > 0 and not r.get("producer")]
    isolated = [r for r in all_records
                if r.get("phase") == "isolated" and r.get("ok")
                and r.get("tbt_p95_s", -1) > 0 and not r.get("producer")]
    if len(shared) < 3 or len(isolated) < 3:
        return ["TBT gate: insufficient TBT records to evaluate"]
    s_p95 = sorted(r["tbt_p95_s"] for r in shared)[len(shared) // 2]
    i_p95 = sorted(r["tbt_p95_s"] for r in isolated)[len(isolated) // 2]
    if s_p95 > i_p95 * 1.10:
        return [f"TBT gate FAILED: shared p95 {s_p95:.4f}s > isolated "
                f"{i_p95:.4f}s * 1.10 (decode-path regression)"]
    return []


EXPERIMENT = Experiment(
    id="t1",
    title="T1: Baseline Matched Evaluation (Qwen3-8B, 8 instances)",
    extra_metrics=[
        ("tbt_p50_s", "TBT p50 (decode, per-token)"),
        ("tbt_p95_s", "TBT p95 (decode, per-token)"),
        ("total_s", "Total latency (full response)"),
    ],
    extra_gates=[("tbt_stability", _tbt_gate)],
)


if __name__ == "__main__":
    run_experiment(EXPERIMENT)
