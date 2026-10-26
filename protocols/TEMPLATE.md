# Protocol Pnn: <short name>

<!--
Commitment 1 of OUTLINE.md. This file is written and committed BEFORE any
result it describes exists. `tools/check_protocols.py` compares the commit
date of this file against the `captured` date of every artifact it names,
and fails the build if a result predates its protocol.

That check is the whole mechanism. A protocol written afterwards is a
description; a protocol written beforehand is a commitment, and only the
commit history can tell the two apart.

Copy this file, fill every field, commit it, and only then run anything.
-->

- **Status:** DRAFT | COMMITTED | RUN | REPORTED
- **Chapter:** <n>
- **Registered:** <YYYY-MM-DD>
- **Artifacts:** <names in data/results/, without the .json>

## The question

One sentence, stated so that every possible answer is reportable.

## Circuits and noise

Which circuits, at which distances and angles, under which noise model,
with every parameter named. A circuit or noise setting added after seeing
results is a different protocol.

## Method

Sampler, post-selection rule, decoder, and what counts as a logical error.

## Budget

- Shots per point, and the interval width that buys
- Seeds: the base seed and how batch seeds derive from it
- Ceiling: the compute at which this run stops regardless of result

## Metrics and acceptance criteria

- Primary metric: one, chosen now
- Interval: 95% Wilson
- Pass/fail criterion, numeric, written before running

## Stopping rule

When the run ends. Written now so it cannot become "when the result looked
right".

## What each outcome means

Fill in **before** running. If a result can be narrated either way after
the fact, it is not evidence.

- If it passes: <what that does and does not establish>
- If it fails: <what happens next>
- If it is underpowered: <what happens — this is not a null result>

## Deviations

Anything that changed after registration, dated, with its reason. An empty
section is the goal; a dishonest empty section is the failure this whole
mechanism exists to make visible.
