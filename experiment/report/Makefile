DOC_NAME=execution-cycles

MAIN=execution-cycles
TEX=$(MAIN).tex
AUX=$(MAIN).aux
PDF=$(MAIN).pdf
BBL=$(MAIN).bbl

BIB=thebibliography.bib

.PHONY: clean doc

doc: $(PDF)

$(PDF): $(TEX)
	latexmk -pdf -pdflatex="pdflatex -shell-escape -interaction=nonstopmode" -use-make $(TEX)

clean:
	latexmk -CA
