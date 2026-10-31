PYTHON ?= python3
.PHONY: verify figures paper bundles
verify:
	$(PYTHON) tools/offline/verify_evidence.py
figures:
	$(PYTHON) tools/offline/make_figures.py
paper: verify
	cd paper && pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
	cd paper && bibtex main
	cd paper && pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
	cd paper && pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
bundles: paper
	$(PYTHON) tools/offline/package_release.py
