"""Chunked, parallel sampling with an error-count stopping rule.

The scheduler P02 introduced (tools/measure_p02.py, left unchanged as part
of that protocol's record), generalised so a runner passes its own points.
Each point runs in fixed-size chunks with fixed seeds. It stops at the
first chunk where its cumulative errors reach the target, or at its cap;
chunks the pool computed beyond that are discarded, so the estimate does
not depend on scheduling.
"""

from __future__ import annotations

import multiprocessing as mp
import time


def run(points: dict, worker, *, workers: int = 10,
        ceiling_s: float = 2.5 * 3600, inflight: int = 3) -> dict:
    """Sample every point; return {key: (stopped_by, [(errors, accepted)])}.

    `points` maps a key to {"chunk": shots, "target": errors, "cap": shots,
    "seed": f(chunk)}. `worker((key, chunk, shots, seed))` must be a
    top-level function returning (task, errors, accepted).
    """
    state = {k: {"done": {}, "next": 0, "stopped": None} for k in points}
    start = time.time()
    with mp.get_context("spawn").Pool(workers) as pool:
        pending = set()

        def submit(key):
            spec, chunk = points[key], state[key]["next"]
            state[key]["next"] += 1
            pending.add(pool.apply_async(
                worker, ((key, chunk, spec["chunk"], spec["seed"](chunk)),)))

        def settle(key):
            s, spec, errors, c = state[key], points[key], 0, 0
            while c in s["done"] and s["stopped"] is None:
                errors += s["done"][c][0]
                if errors >= spec["target"]:
                    s["stopped"] = ("errors", c)
                elif (c + 1) * spec["chunk"] >= spec["cap"]:
                    s["stopped"] = ("cap", c)
                c += 1

        for key in points:
            submit(key)
        while pending:
            time.sleep(1)
            for result in [r for r in pending if r.ready()]:
                pending.remove(result)
                (key, chunk, _, _), errors, accepted = result.get()
                s, spec = state[key], points[key]
                was = s["stopped"]
                s["done"][chunk] = (errors, accepted)
                settle(key)
                if s["stopped"] is None:
                    if time.time() - start > ceiling_s:
                        prefix = 0
                        while prefix in s["done"]:
                            prefix += 1
                        s["stopped"] = ("ceiling", prefix - 1)
                    else:
                        for _ in range(max(0, inflight
                                           - (s["next"] - len(s["done"])))):
                            if s["next"] * spec["chunk"] < spec["cap"]:
                                submit(key)
                if s["stopped"] and not was:
                    print(f"{key} stopped ({s['stopped'][0]}) after "
                          f"{s['stopped'][1] + 1} chunks, "
                          f"{time.time() - start:6.0f}s", flush=True)
    return {k: (s["stopped"][0],
                [s["done"][c] for c in range(s["stopped"][1] + 1)])
            for k, s in state.items()}
