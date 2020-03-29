# Convert log files to CSV with observations, 1 line per core
LOG_DIR=output
LOG_FILES=$(shell find $(LOG_DIR) -name "*.log")
CSV_FILES=$(patsubst %.log,%.csv,$(LOG_FILES))
DATA_DIR=report/data

CSV_SUMMARIES=$(shell find $(DATA_DIR) -name "*.csv")
TEX_SUMMARIES=$(patsubst %.csv,%.tex,$(CSV_SUMMARIES))
TEX_INPUT=report/input-figures.tex

.phony: run clean

define CSV2SUMMARY
	python csv2summary.py --input-file=$(1) --output-directory=$(DATA_DIR);
endef

run: $(CSV_FILES) $(TEX_SUMMARIES) $(TEX_INPUT)
	$(foreach csv_file,$(CSV_FILES),$(call CSV2SUMMARY,$(csv_file)))

$(CSV_FILES): $(LOG_FILES)
	$(eval LOG := $(patsubst %.csv,%.log,$@))
	awk -f log2csv.awk $(LOG) > $@

$(TEX_SUMMARIES): $(CSV_SUMMARIES)
	$(eval TEX := $(patsubst %.csv,%.tex,$@))
	$(eval CSV := $(patsubst %.tex,%.csv,$(TEX)))
	$(eval INPUT := `echo $(CSV)|sed 's/^report\///'`)
	$(eval CFG := `echo $(TEX)|sed 's/^.*config\([0-9]*\).*/\1/'`)
	$(eval FT := `echo $(TEX)|sed 's/^.*config[0-9]*-\([a-z]*\).*/\1/'`)
	$(eval FC := `echo $(TEX)|sed 's/^.*config[0-9]*-[a-z]*\([0-9]*\).*/\1/'`)
	@echo "csv is "$(CSV)
	@echo "tex is "$(TEX)
	@echo "config is "$(CFG)
	@echo "fixedtype is "$(FT)
	@echo "fixedconf is "$(FC)
	@echo "inputfile is "$(INPUT)
	m4 -Dfilename=$(INPUT) \
		-Dconfig=$(CFG) -Dfixedtype=$(FT) -Dfixedconf=$(FC) maketex-cyclesummaries.m4 > $@

do: $(TEX_INPUT)

$(TEX_INPUT): $(TEX_SUMMARIES)
	@echo $(TEX_SUMMARIES) | \
		tr " " "\n" | \
		sed 's/^report\///' | \
		awk '{printf("\\input{%s}\n", $$1)}' | sort -n > $@

clean:
	rm -f $(CSV_FILES) $(CSV_SUMMARIES) $(TEX_SUMMARIES) $(TEX_INPUT)
