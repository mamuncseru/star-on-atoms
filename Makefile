# Build and verify STAR on Atoms.
#
# `make check` is what CI runs and what should pass before every commit. It
# is ordered cheapest-first, so a mistake is reported in seconds rather than
# after a full render.

QUARTO ?= $(shell command -v quarto 2>/dev/null || echo $(HOME)/opt/quarto-1.10.18/bin/quarto)
PYTHON ?= $(shell test -x $(HOME)/.venvs/star-book/bin/python && echo $(HOME)/.venvs/star-book/bin/python || echo python3)

# Run Quarto's Jupyter engine from the book's own environment. Left to find
# `python3` on PATH, it started from a shared lab environment and the
# chapters could not import tsim, although the star-book kernelspec was
# correct (found on the first render, 2026-10-26).
export QUARTO_PYTHON := $(PYTHON)

.PHONY: help check release fetch reference citations math structure citekeys \
        results protocols test code kernel book html pdf clean

help:
	@echo "make fetch      download QuEra's STAR circuits, pinned + hash-checked"
	@echo "make reference  digitize QuEra's reference plot into data/reference/"
	@echo "make check      run every offline guard (what CI runs on a push)"
	@echo "make release    check + verify every citation + full render"
	@echo "make book       render website + PDF into book/_book/"
	@echo "make html       render the website only (fast)"
	@echo "make pdf        render the PDF only"
	@echo "make kernel     register the star-book Jupyter kernel + capture env"
	@echo "make clean      remove render output and the freeze cache"

# --- inputs ------------------------------------------------------------------

fetch:
	@$(PYTHON) tools/fetch_star_circuits.py

reference: fetch
	@$(PYTHON) tools/digitize_reference.py

# --- guards, cheapest first --------------------------------------------------

check: math structure citekeys results protocols test code
	@echo
	@echo "All offline guards passed."

# The release gate. `citations` needs the network, so it is deliberately not
# part of `check`: a guard that fails on a train is a guard people disable.
release: check citations book
	@echo
	@echo "Release gate passed: guards, bibliography, and a full render."

citations:
	@echo "== every DOI and arXiv ID resolves to the paper we cite =="
	@$(PYTHON) tools/check_citations.py --require-all

math:
	@echo "== Typst-safe maths =="
	@$(PYTHON) tools/test_check_math.py
	@$(PYTHON) tools/check_math.py

structure:
	@echo "== every chapter keeps the contract =="
	@$(PYTHON) tools/check_structure.py

citekeys:
	@echo "== every cited key exists in the bibliography =="
	@$(PYTHON) tools/check_citekeys.py

results:
	@echo "== every committed measurement carries its evidence =="
	@$(PYTHON) tools/check_results.py

protocols:
	@echo "== every protocol was committed before its results =="
	@$(PYTHON) tools/check_protocols.py

test: fetch
	@echo "== starlab =="
	@$(PYTHON) tests/test_starlab.py

code:
	@echo "== listings, the palette, companion scripts =="
	@$(PYTHON) tools/check_code.py

# --- environment -------------------------------------------------------------

kernel:
	@$(PYTHON) tools/install_kernel.py

# --- rendering ---------------------------------------------------------------

book: fetch
	$(QUARTO) render book

html: fetch
	$(QUARTO) render book --to html

pdf: fetch
	$(QUARTO) render book --to typst

clean:
	rm -rf book/_book book/.quarto book/_freeze
