# Build the paper. Requires a TeX distribution with the target venue's class.
#
#   make            build main.pdf
#   make clean      remove build artefacts
#   make watch      rebuild on change (needs latexmk)

MAIN = main

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex preamble.tex refs.bib $(wildcard sections/*.tex) $(wildcard figures/*.pdf)
	latexmk -pdf -interaction=nonstopmode -halt-on-error $(MAIN).tex

watch:
	latexmk -pdf -pvc -interaction=nonstopmode $(MAIN).tex

clean:
	latexmk -C
	rm -f $(MAIN).bbl $(MAIN).run.xml *.aux sections/*.aux

.PHONY: all watch clean
