"""Sample a STAR circuit, post-select, decode, count.

The pipeline Protocol P01 registers, in one place:

1. Sample detectors and the logical observable with tsim.
2. Accept a shot only if the first 3(d^2 - 1) detectors are all zero (the
   injection rounds).
3. Decode every accepted shot's full detector record with minimum-weight
   perfect matching on the circuit's own detector error model.
4. A logical error is a decoded observable that disagrees with the
   measured one.

One seeded sampler is compiled per run and drawn from in fixed-size
batches, so a run is repeatable exactly from its seed and batch size.
"""

from __future__ import annotations

import numpy as np

from .circuits import n_postselected, star_circuit
from .stats import rate_record


def matcher(circuit):
    """A PyMatching decoder built from the circuit's Clifford proxy.

    tsim will not decompose a detector error model whose observable is
    non-deterministic, and matching needs a decomposed one. But stim reads
    tsim's rotations as tagged identities, so `circuit.stim_circuit` is the
    same circuit at theta = 0: Clifford, with a deterministic observable.
    Its error model is exact for every Pauli error after the injection
    layer -- the d memory rounds the decoder is responsible for. Errors
    before or during injection are the post-selection's job, not its.
    """
    import pymatching

    dem = circuit.stim_circuit.detector_error_model(decompose_errors=True)
    return pymatching.Matching.from_detector_error_model(dem)


def sample_star(d: int, theta_rad: float, shots: int, seed: int,
                batch: int = 100_000, circuit=None) -> dict:
    """Run the P01 pipeline; return counts with their Wilson intervals."""
    circuit = circuit if circuit is not None else star_circuit(d, theta_rad)
    decoder = matcher(circuit)
    post = n_postselected(d)
    # Compile once: tsim's JAX compilation dominates small runs. The seeded
    # sampler's stream then advances batch by batch, so the run is
    # repeatable from (seed, batch) alone.
    sampler = circuit.compile_detector_sampler(seed=seed)
    accepted = errors = done = 0
    batch_index = 0
    while done < shots:
        n = min(batch, shots - done)
        dets, obs = sampler.sample(n, separate_observables=True)
        dets, obs = np.asarray(dets, dtype=bool), np.asarray(obs, dtype=bool)
        keep = ~dets[:, :post].any(axis=1)
        if keep.any():
            predicted = decoder.decode_batch(dets[keep]).astype(bool)
            errors += int((predicted[:, 0] != obs[keep, 0]).sum())
            accepted += int(keep.sum())
        done += n
        batch_index += 1
    record = rate_record(errors, accepted)
    record.update({"d": d, "theta_rad": theta_rad, "shots_sampled": shots,
                   "acceptance": accepted / shots, "seed": seed,
                   "batch_size": batch, "batches": batch_index})
    return record


def sample_injection(circuit, shots: int, seed: int,
                     batch: int = 100_000) -> dict:
    """The injection error, decoder-free (Protocols P02, P03).

    Accept a shot only if every detector is zero. With noise confined to the
    injection window, the later rounds are perfect stabilizer measurements,
    so an accepted shot carries no detectable error at all, and a flipped
    observable is an error post-selection cannot see. No decoder, no floor.
    """
    sampler = circuit.compile_detector_sampler(seed=seed)
    accepted = errors = done = batches = 0
    while done < shots:
        n = min(batch, shots - done)
        dets, obs = sampler.sample(n, separate_observables=True)
        keep = ~np.asarray(dets, dtype=bool).any(axis=1)
        errors += int(np.asarray(obs, dtype=bool)[keep, 0].sum())
        accepted += int(keep.sum())
        done += n
        batches += 1
    record = rate_record(errors, accepted)
    record.update({"shots_sampled": shots, "acceptance": accepted / shots,
                   "seed": seed, "batch_size": batch, "batches": batches})
    return record
