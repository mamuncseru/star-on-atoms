# Protocol P03: the exact first-order injection error, tested against P02

- **Status:** REPORTED
- **Chapter:** 12
- **Registered:** 2026-10-27
- **Artifacts:** p03_exact_vs_p02

## The question

Does `starlab.enumerate`, with no free parameter, reproduce the injection
error that P02 sampled from 665 million shots?

`starlab.enumerate` is an exact first-order evaluation of the paper's Eq. 2
for these circuits. For every fault mechanism, it matches the fault's
detector symptom against the 2^k rotation branches. It is to be tested at
all 32 of P02's points and on its four (distance, model) constants.

If it does, the per-channel error budget (P04) and other distances can be
computed exactly and sampled only to test that computation. If it does not,
sampling stays primary.

## Circuits and noise

- **Exactly P02's circuits.** They come from `tools/measure_p02.build`
  (unchanged since P02's registration, commit `d1e9934`):
  - models U and T on the angle grid θ = π/2ⁿ, n = 2 … 7, at d = 3 and 5;
  - the four T variants at π/16;
  - noise only in the injection window.
- **The calculator:** `starlab/enumerate.py` at commit `5b6cd6a` (git blob
  `37912c9014cb2355405ac6aaebaef18d1c52ccc1`), with the runner
  `tools/measure_p03.py` committed with this protocol.

## Method

1. For each circuit, take the θ = 0 Clifford proxy (`tsim` → `stim_circuit`)
   and its detector error model: undecomposed, with
   `approximate_disjoint_errors=True`.
2. A marker Z after the R_Z on each rotated qubit gives the branch
   symptoms. Every symptom class must be exactly {S, K − S}; the code
   asserts this.
3. A fault survives if its symptom is a branch symptom. The X_L bit picks
   S*, and the fault contributes p × `branch_weight(θ, k, |S*|)`. The
   predicted injection error is the sum of these contributions.
4. For each (d, model), A_C is formed exactly as P02 formed its A:
   Σ (predicted rate × P02's accepted) ÷ Σ (P02's accepted × f_d).

**Disclosure.** P02's data were known when this protocol was written; its
committed counts are the reference. The calculator has no parameter fitted
to them. The unit tests in `tests/test_starlab.py` were run before
registration, and use only planted single faults in noiseless circuits.

## Budget

Deterministic: seconds per circuit. No seeds. No ceiling is needed.

## Metrics and acceptance criteria

- **Primary:** the ratio A_C / A_P02 for each of the four (d, model) pairs,
  plus the variant ratios.
- **CONFIRMED** if both hold:
  - all four ratios lie in ×[0.92, 1.08];
  - the predicted variant ratio (variant ÷ T at π/16) lies inside P02's
    Katz 95% interval for at least 7 of the 8 variants.
- **REFUTED** if any of the four ratios lies outside ×[0.85, 1.18].
- **INCONCLUSIVE** otherwise.

Why these windows: P02's pooled statistics give about ±4% at 95%. The
first-order calculation leaves out a normalization term of about 1% and a
second-order term estimated at ≲ 2%. A narrower window would refute a
correct first-order theory on known higher-order terms.

**Reported, not pass/fail:**
- χ² of P02's 32 grid counts against the predicted counts (32 dof);
- the census of mechanisms (detected, harmless, matched);
- the share of the predicted error carried by m = 1 faults (prediction
  registered now: ≥ 99%);
- first-order additivity: Σ over Table II rows (one error model per row)
  ÷ all-on, at π/16.

## Stopping rule

One deterministic pass over the 32 points. There is no rerun.

## What each outcome means

- **CONFIRMED:** the injection error of these circuits is understood to
  first order, fault by fault.
  - P04 registers the calculator's per-row predictions (d = 3, 5 and 7)
    before sampling them, as a blind test.
  - The budget, the per-CZ-term sensitivities and the other distances come
    from the calculator. Sampling checks them.
- **REFUTED:** a mechanism outside first-order branch-matching matters, or
  the calculator is wrong.
  - P04 falls back to the sampled budget as drafted (option A).
  - The calculator becomes a diagnostic: the misses point to the missing
    mechanism.
- **INCONCLUSIVE:**
  - P04 samples every row (option A), and still reports the calculator's
    predictions next to them.
  - Before claiming anything exact, the gap is explained (second order?
    normalization?).
- **Deadline (decision log, 2026-10-27):** if P03 is not CONFIRMED by
  Thu 10-29 12:00, P04 runs as option A.

## Deviations

**2026-10-27, wording.** "Reported, not pass/fail" calls the χ² test
"P02's 32 grid counts … (32 dof)". P02 has 24 grid points plus 8 variant
points. The runner computed χ² over the 24 grid points (24 dof). Both
versions are reported below. Neither is a criterion.

**2026-10-27, after the run: the result.** One deterministic pass, 3.8 s
in total. No deviation from method.

- **CONFIRMED.**

  | d | Model | A_C/p | A_P02/p | Ratio (window ×[0.92, 1.08]) |
  |---|---|---|---|---|
  | 3 | U | 6.256 | 6.441 | 0.971 |
  | 3 | T | 3.424 | 3.411 | 1.004 |
  | 5 | U | 8.588 | 8.542 | 1.005 |
  | 5 | T | 4.693 | 4.925 | 0.953 |

  Variants: **8/8** predicted ratios inside P02's Katz intervals:
  - T-naiveH: 1.234 (d = 3), 1.228 (d = 5);
  - T-datamove: 1.041, 1.036;
  - T-pairloss: 1.000, 1.000;
  - T-ffnoise: 1.156, 1.171.
- **Reported.**
  - **χ²:** 27.0 over the 24 grid points (p = 0.30); 35.0 over all 32
    points (p = 0.33).
  - **m = 1 share: 100% at every point.** No fault at m ≥ 2 survives at
    all, beyond the registered ≥ 99%.
  - **Census at π/16, Table II:** 3 of 271 symptom classes survive at
    d = 3, and 5 of 955 at d = 5, one per rotated qubit. Every other
    mechanism is detected.
  - **Additivity over Table II rows:** Σ ÷ all-on = 1.0008 (d = 3),
    1.0007 (d = 5).
  - **Residual at π/128, uniform model:** P02 lies above C by 14% at
    d = 3, outside P02's Wilson interval, and by 8% at d = 5, inside it.
    This is the expected sign of a second-order, θ-independent term. It
    shows first only where first order is smallest.
