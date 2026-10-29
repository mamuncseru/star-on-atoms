# Progress

The project's log, newest first. The
[home page](https://mamuncseru.github.io/star-on-atoms/) is built from this
file: its "Now" section, its milestone table (drawn as a timeline) and its
three newest log entries. When the project moves, this is the one file to
edit.

## Now

**Ready to freeze.** The three-page note is written
([`note/`](note/star-on-atoms-note.qmd)), and the README leads with the
answer. The prior-art reading is done. It narrowed one claim and sharpened
another: in these circuits the rotation gate itself carries only 12–16% of
the injection error.

**Next:** the first mock interview, then the **freeze on Fri 2026-10-30**:
`make release`, the book and note PDFs on the site, and each chapter's
Agent Log ticked by the author or the chapter left out.

## Milestones

| Date | Milestone | Status |
|---|---|---|
| 2026-10-26 | Pipeline, guards and book scaffold; P01 registered and run | ✅ |
| 2026-10-27 | P01 explained: the reference's decoder (R6) and a read-out artifact (R7) | ✅ |
| 2026-10-27 | Re-noiser validated against the published error model; P02 registered | ✅ |
| 2026-10-27 | P02 reported: one constant times the misrotation shape fits both noise models | ✅ |
| 2026-10-27 | P03: an exact first-order calculation reproduces P02 with no free parameter | ✅ |
| 2026-10-28 | P04: the sampled error budget, a blind test of the calculation (d = 3, 5, 7) | ✅ |
| 2026-10-28 | Error-budget chapter and its headline figure; threats to validity | ✅ |
| 2026-10-29 | A short note (3 pages) and the README headline; prior art read | ✅ |
| 2026-10-29 | Mock interview #1 | ⬜ |
| 2026-10-30 | Freeze: results final, book PDF released | ⬜ |

## Log

### 2026-10-29 · The note; the rotation gate is a minority of its own error

-   **The prior art, read.** Two earlier papers already count undetected
    single faults at first order: Choi *et al.* (2303.17380) and the
    original STAR paper (Toshio *et al.*, 2408.14848, Eq. 12).
    -   So the claim is narrowed to what is new here: a mechanical count,
        channel by channel, over every fault in QuEra's published
        circuits, tested blind.
-   **The rotation gate is a minority.** The STAR paper treats the
    rotation gate's errors as the only undetectable ones. In these
    circuits that gate carries only 11.7% of the injection error at
    d = 3 (18.2% at d = 15).
    -   The rest of the single-qubit share is the Hadamards that the
        CNOT-to-CZ compilation leaves on data qubits.
    -   Halving the rotation gate's error alone buys ×1.08 in simulation
        volume. Halving every single-qubit gate buys ×1.32.
-   **The note.** A three-page summary for readers who will not open the
    book: the answer in four points, the method and its prior art, the
    blind test, the budget, a sourced table of the paper's open readings,
    and the limits. Its numbers come straight from the committed results.
-   **The README** now leads with the answer.

### 2026-10-28 · The blind test passes; the CZ's largest error is free

-   **[P04](protocols/P04-sampled-budget-blind-test.md) CONFIRMED.** Every
    prediction was committed before sampling (552 million shots, 79
    minutes).
    -   On all nine main arms, measured ÷ predicted lies between 0.95 and
        1.10.
    -   **d = 7, never sampled before:** 2.60×10⁻⁴ measured against
        2.53×10⁻⁴ predicted.
    -   Rows the calculation puts at exactly zero (initialization,
        measurement, loss) sample a few errors, all below 0.7% of the
        total. So they are zero at first order, not zero.
-   **What halving buys.** Halving single-qubit-gate error multiplies the
    simulation volume by 1.32 at d = 5. Sampled: 1.36 (1.21–1.52).
    Halving spectator or CZ error buys 1.13–1.18.
-   **Inside the CZ ([R1](protocols/P04-sampled-budget-blind-test.md),
    CONFIRMED).** The CZ's correlated *ZZ* error, its largest term, costs
    this injection nothing: 2 errors in 11 million accepted shots.
    -   Every ancilla is prepared and measured in *X*, so the ancilla half
        of a *ZZ* is always caught. A new test checks this one planted
        fault at a time.
    -   The same test found a piece the registration missed: an *X* on an
        ancilla also hides, by spreading to the data.
-   **Where first order bends.** At today's full hardware rates it is
    10% low. The derivation in the threats chapter turns that into about
    1% at the operating point.
-   Chapters [12](book/chapters/part4/ch12-error-budget.qmd) (the error
    budget) and [13](book/chapters/part4/ch13-threats.qmd) (threats to
    validity) are drafted.

### 2026-10-27 (late night) · No GPU; an exact calculation instead

-   **The GPU question.** Four NVIDIA A40s are available. The principle:
    add a tool only if it is really useful.
    -   Both advisors, consulted independently, said no GPU before
        submission, and the facts agree. The planned runs take hours on
        CPU, and the simulator generates its noise on the CPU, which caps
        any GPU gain.
    -   The GPU is kept for later work that needs 10⁹–10¹⁰ shots, once a
        profile, a speed-up test and a re-run of a P02 point have passed.
-   **What replaced it.** P02 showed that the injection error comes from
    single faults that a rotation branch hides. So each fault can be
    matched against the branches directly:
    -   [`starlab/enumerate.py`](starlab/enumerate.py) does this in the
        circuit's own error model. In seconds, at any distance, with no
        sampling, it gives the injection error to first order. That is the
        paper's Eq. 2, evaluated exactly.
-   **[P03](protocols/P03-exact-first-order.md) CONFIRMED.** With no
    fitted parameter, the calculation reproduces P02's four sampled
    constants (ratios 0.97, 1.00, 1.01, 0.95) and all 8 variant ratios
    (χ² p = 0.30).
    -   Only 3 of 271 fault classes survive post-selection at d = 3 (5 of
        955 at d = 5), each one a single *Z* on a rotated qubit.
    -   **Initialization, measurement and atom loss cost exactly nothing
        in fidelity**, only shots.
-   **The first-order budget at π/16 under Table II:**
    -   single-qubit gates 43–48%;
    -   spectators 26–31%;
    -   the CZ 25–26%;
    -   moves 0.5%.
-   **[P04](protocols/P04-sampled-budget-blind-test.md)** was registered
    with every prediction committed, and launched.

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
