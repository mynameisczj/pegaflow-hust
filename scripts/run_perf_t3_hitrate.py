#!/usr/bin/env python3
"""
run_perf_t3_hitrate.py — T3: hit-rate sensitivity.

Controls cross-instance hit rate by prefix ratio: the warmup seed stores the
full prompt; the Q0 test prompt shares only the first `ratio` fraction of the
system block (rest is a distinct suffix), so prefetch hits ~ratio of blocks.

Preregistered (perf plan §T3):
  - ratios: 50 / 75 / 90 / 100 (%)
  - gate: measured Q0 hit_blocks/76 must land within +/-5pp of target,
    else the run is INVALID (controls the manipulation actually worked)
  - deliverable: break-even vs hit rate; the crossover hit-rate threshold
    where prefill_saved <= dma_cost

Usage:
  python scripts/run_perf_t3_hitrate.py [--ratios 50,75,90,100] [--dry-run]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_perf_base import Experiment, run_experiment, SYSTEM_PROMPT

# One system block ~= 250 tokens; full seed = 38 blocks (~10k tokens).
_BLOCKS = 38
HIT_BLOCKS_EXPECTED = 76  # Qwen3-8B 76-block KV footprint at 10k tokens

RATIOS = [50, 75, 90, 100]


def _make_ratio_prompts(ratio: int):
    """Return (warmup_prompt, test_prompt).

    Warmup seeds the full system block (~10k tokens). The test prompt keeps
    the first `ratio`% of the system block identical (those blocks hit) and
    replaces the remainder with distinct filler of the same length (those
    blocks miss) — total length stays ~10k so prefill cost is comparable
    while only the hit fraction varies.
    """
    full = SYSTEM_PROMPT
    suffix = "\n\nUser: What is the capital of France?\n\nAssistant:"
    cut = int(len(full) * ratio / 100)
    filler_len = len(full) - cut
    filler = ("DIFFERENT CONTENT PARAGRAPH. " * (filler_len // 28 + 1))[:filler_len]
    test = full[:cut] + filler + suffix
    return full + suffix, test


def _hitrate_gate(target: int):
    def gate(all_records, merge_result):
        # Cross-instance hits only: vLLM-local prefix-cache hits (local_hit)
        # are 100% by construction and would bias the mean.
        shared = [r for r in all_records
                  if r.get("phase") == "shared" and r.get("ok")
                  and not r.get("producer") and r.get("query_idx") == 0
                  and not r.get("local_hit")]
        if not shared:
            return ["T3 gate: no cross-instance shared Q0 records"]
        hits = [r.get("hit_blocks", 0) for r in shared]
        measured = (sum(hits) / len(hits) / HIT_BLOCKS_EXPECTED) * 100.0
        if abs(measured - target) > 5.0:
            return [f"T3 gate FAILED: measured hit rate {measured:.1f}% "
                    f"vs target {target}% (deviation > 5pp)"]
        return []
    return gate


def main():
    ratios = RATIOS
    args = []
    ratio_arg = None
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--ratios":
            ratio_arg = argv[i + 1]
            i += 2
            continue
        if a.startswith("--ratios="):
            ratio_arg = a.split("=", 1)[1]
            i += 1
            continue
        args.append(a)
        i += 1
    if ratio_arg:
        ratios = [int(r) for r in ratio_arg.split(",")]

    for ratio in ratios:
        warmup_p, test_p = _make_ratio_prompts(ratio)

        def prompt_fn(q, qi, _r=ratio, _w=warmup_p, _t=test_p):
            # qi == -1 is the warmup seed (full prompt); Q0 is the test prompt.
            if qi == -1:
                return _w
            if qi == 0:
                return _t
            return f"{SYSTEM_PROMPT}\n\nUser: {q}\n\nAssistant:"

        exp = Experiment(
            id=f"t3-h{ratio}",
            title=f"T3: hit rate {ratio}% (prefix manipulation)",
            cycles=1,
            requests_per_phase=1,   # only Q0 matters for hit rate
            warmup_first=True,
            prompt_fn=prompt_fn,
            extra_gates=[("hitrate", _hitrate_gate(ratio))],
            extra_metrics=[("total_s", "Total latency (full response)")],
        )
        print(f"\n{'='*70}\nT3 ratio: {ratio}%\n{'='*70}")
        run_experiment(exp, argv=args)


if __name__ == "__main__":
    main()
