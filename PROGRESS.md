# Progress

The project's log, newest first. The
[home page](https://mamuncseru.github.io/star-on-atoms/) is built from this
file: its "Now" section, its milestone table (drawn as a timeline) and its
three newest log entries. When the project moves, this is the one file to
edit.

## Now

**P02 is reported: one constant fits.** Under both QuEra's Table II
hardware model and the published uniform model, the injection error of the
published circuits is a single constant times the paper's misrotation term,
evaluated exactly. It holds from π/4 to π/128 at d = 3 and 5, flat to
within 15% over a 150–400× range in rate. At the same headline error
$p_{\text{ph}} = 10^{-3}$, the hardware model gives about **half** the
uniform model's injection error. See the [ledger](LEDGER.md).

**Next:** Protocol P03, the error budget. Because a channel can change only
the constant, never the angle dependence, the budget can be measured at one
angle. Each Table II channel is switched on alone, giving its share of the
injection error and so of α.

## Milestones

| Date | Milestone | Status |
|---|---|---|
| 2026-10-26 | Pipeline, guards and book scaffold; P01 registered and run | ✅ |
| 2026-10-27 | P01 explained: the reference's decoder (R6) and a read-out artifact (R7) | ✅ |
| 2026-10-27 | Re-noiser validated against the published error model; P02 registered | ✅ |
| 2026-10-27 | P02 reported: one constant times the misrotation shape fits both noise models | ✅ |
| 2026-10-28 | P03: the error budget, one noise channel at a time | 🚧 |
| 2026-10-31 | Error-budget chapter and its headline figure | ⬜ |
| 2026-11-02 | A short note (2–3 pages); threats to validity | ⬜ |
| 2026-11-04 | Freeze: results final, book PDF released | ⬜ |

## Log

### 2026-10-27 (night) · P02 reported: one constant fits; hardware noise halves the error

-   **[P02](protocols/P02-renoise-table-ii.md)** ran in 35 minutes:
    665 million shots, 32 points, each to 400 errors or its cap.
-   **The registered shape test passed (H2 CONFIRMED).** In every
    (distance, model) pair, the injection error divided by the paper's
    misrotation term varies by at most ×1.15 from π/4 to π/128 (the limit
    was ×1.5). A noise channel can change only the constant in front.
-   **QuEra's hardware model at $p_{\text{ph}} = 10^{-3}$ gives 0.53×
    (d = 3) and 0.58× (d = 5) the uniform model's injection error.** Only a
    net pure-*Z* on the data survives post-selection. Table II puts more
    *Z* into the CZ than uniform noise does, but much less into spectators,
    single-qubit gates and idles. P03 will test that explanation.
-   **The paper's open readings, priced** (at π/16):
    -   keeping every Hadamard from the CNOT-to-CZ compilation: +20–25%;
    -   a physical (noisy) feed-forward before the rotation: +15%;
    -   moving the data atom instead of the ancilla: no measurable change;
    -   loss on the gate pair only: no change in error, more shots
        accepted. Loss costs acceptance, not fidelity.
-   Through the paper's Eq. 4, these teaching circuits have α ≈ 8.5 under
    Table II; the paper's own optimised protocol reaches α ≈ 1.5 at d = 7.
-   **[Chapter 11](book/chapters/part4/ch11-renoising.qmd)** tells the
    story, with the evidence table and the figure.

### 2026-10-27 (evening) · Re-noiser validated; P02 registered and running

-   [`starlab/renoise.py`](starlab/renoise.py) rebuilds each published
    circuit on CZ and single-qubit gates. It puts every Table II channel
    where its process happens:
    -   moves before a CZ;
    -   the CZ's two-qubit Pauli channel and its loss after it;
    -   spectator errors on unpaired atoms;
    -   bit flips before measurements.
-   **Validation.** Given the published uniform noise, the rebuild
    reproduces the published detector error model exactly: every fault
    probability agrees to 10⁻¹⁵, at d = 3, 5 and 7, for all four
    compilation variants. Removing any one placement rule breaks the match.
-   **[Protocol P02](protocols/P02-renoise-table-ii.md)**, registered
    before its first sample, measures the injection error:
    -   Table II scaled to $p_{\text{ph}} = 10^{-3}$;
    -   noise only in the injection window, every detector post-selected,
        no decoder;
    -   four variants for the readings the paper leaves open.
-   **Theory, with credit.** The paper's Eq. 2 names the leading injection
    error, a "coherent misrotation" of order $p\,\theta^{2(1-1/k)}$. The
    book evaluates that term exactly for the published circuits, and checks
    it by planting a single *Z* fault.
-   **[Chapter 8](book/chapters/part3/ch08-the-noise-menu.qmd)** pins
    Table II from the PDF. Its Eq. D1 sums to 7.46 × 10⁻³; the paper quotes
    "≈ 7.3 × 10⁻³".
-   **[Chapter 9](book/chapters/part3/ch09-from-injection-to-alpha.qmd)**:
    composed through the paper's Eq. 4, the teleported error is linear in
    θ. The injections at π/4 to π/16 set most of α: 61% at k = 3, 79% at
    k = 5.

### 2026-10-27 · P01 explained: a decoder and a read-out artifact

-   [P01](protocols/P01-reproduce-uniform-star.md) failed as registered: a
    geometric-mean ratio of 0.375 against QuEra's published curve, where
    the window was 0.80–1.25. The verdict stays in the [ledger](LEDGER.md).
-   The diagnosis, every step registered before it ran:
    -   **R6.** Decoding the same samples by matching on tsim's default
        (undecomposed) error model reproduces the published curve (ratio
        1.10). PyMatching silently drops that model's faults that flip
        more than two detectors: 19% of the fault probability at d = 3. A
        correctly decomposed model gives a d = 3 floor about 9× lower.
    -   **R7.** At large angles, the published circuits mostly measure
        memory-round *X* errors, read out through the perfect unrotation
        (∝ sin²θ): 69–84% of the angle-dependent error. So later protocols
        measure the injection window alone.
-   Corrected from the PDF: simulation volume scales as 1/(αp), circuit
    volume as 1/(αp)².
-   [Chapter 10](book/chapters/part4/ch10-reproducing-queras-curve.qmd)
    tells the whole story.

### 2026-10-26 · Started

-   The repository and its guards:
    -   pre-registration, checked against commit dates;
    -   every rate carries its shots, seed and Wilson interval;
    -   every equation is compiled through Typst.
-   The book scaffold, with a crash course on the topics the project rests
    on:
    -   codes and transversal gates, magic states, Rydberg atoms, and
        Trotter and Jordan–Wigner (Chapters 2–5);
    -   STAR from first principles (Chapter 6);
    -   detectors and decoding (Chapter 7).
-   [P01](protocols/P01-reproduce-uniform-star.md) registered and run: does
    this pipeline reproduce QuEra's published uniform-noise STAR curve?
