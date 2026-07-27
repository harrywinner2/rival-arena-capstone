# Build the paper. Requires a TeX distribution with the target venue's class.
#
#   make            build main.pdf       (venue target; LNCS by default)
#   make full       build main_full.pdf  (complete manuscript, wide measure)
#   make both       build both
#   make check      structural + numeric checks, no TeX needed
#   make clean      remove build artefacts
#   make watch      rebuild main.pdf on change
#
# Debian/Ubuntu toolchain:
#   sudo apt-get install --no-install-recommends texlive-latex-recommended \
#        texlive-latex-extra texlive-fonts-recommended texlive-publishers \
#        texlive-bibtex-extra lmodern latexmk
#   sudo mktexlsr        # refresh the filename database after installing

MAIN = main
FULL = main_full
DEPS = preamble.tex refs.bib $(wildcard sections/*.tex) $(wildcard figures/*.pdf)
LATEXMK = latexmk -pdf -interaction=nonstopmode

all: $(MAIN).pdf

both: $(MAIN).pdf $(FULL).pdf

$(MAIN).pdf: $(MAIN).tex $(DEPS)
	$(LATEXMK) -halt-on-error $(MAIN).tex

full: $(FULL).pdf

$(FULL).pdf: $(FULL).tex $(DEPS)
	$(LATEXMK) -halt-on-error $(FULL).tex

# Runs without TeX; see ../src for both scripts.
check:
	cd .. && python3 src/check_paper.py && python3 src/verify_paper_numbers.py

# Overfull-box report, worst first -- the typographic residue after a build.
boxes: $(MAIN).pdf
	@grep -o 'Overfull \\hbox ([0-9.]*pt' $(MAIN).log \
	  | sed 's/.*(\([0-9.]*\)pt/\1/' | sort -rn | head -10 \
	  | awk '{printf "  %spt too wide\n", $$1}'

watch:
	$(LATEXMK) -pvc $(MAIN).tex

clean:
	latexmk -C $(MAIN).tex || true
	latexmk -C $(FULL).tex || true
	rm -f $(MAIN).bbl $(FULL).bbl *.run.xml *.aux sections/*.aux

.PHONY: all both full check boxes watch clean
