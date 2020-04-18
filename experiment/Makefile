# Convert log files to CSV with observations, 1 line per core
LOG_DIR=output
TXT_LOGS=$(shell find $(LOG_DIR) -name "*.log")
CSV_LOGS=$(patsubst %.log,%.csv,$(TXT_LOGS))
DATA_DIR=report/data

CSV_SUMMARIES=$(shell find $(DATA_DIR) -name "*.csv")
TEX_SUMMARIES=$(patsubst %.csv,%.tex,$(CSV_SUMMARIES))
TEX_SUMMARIES_COMBINED=report/input-figures.tex

.phony: all csv_summaries tex_summaries_combined clean

# Macro that will generate all summary data files in CSV format
define LOG2DATA_AND_SUMMARIES
	python log2data_and_summaries.py --input-file=$(1) --output-directory=$(DATA_DIR) --output-mode=summary;
endef

# Recursive call to make, to make sure that csv_summaries is fully
# completed before tex_summaries_combined is executed.
all: csv_summaries
	make tex_summaries_combined

# $(CSV_SUMMARIES) cannot be a target, because the exact .csv files with
# summary data aren't know beforehand. The python scripts extracts them
# from the data contained in the .csv log files.
#csv_summaries: $(CSV_LOGS) $(TEX_SUMMARIES) $(TEX_SUMMARIES_COMBINED)
csv_summaries: $(CSV_LOGS)
	$(foreach csv_file,$(CSV_LOGS),$(call LOG2DATA_AND_SUMMARIES,$(csv_file)))

# Implicit target: simple 1 to 1 translation for .log to .csv using AWK
$(CSV_LOGS): $(TXT_LOGS)
	$(eval LOG := $(patsubst %.csv,%.log,$@))
	awk -f log2csv.awk $(LOG) > $@

# This can be an implicit target, because all CSV_SUMMARIES are known by now
# For each *.csv summary, a .tex file is generated with a pgfplot figure, that
# is to be included into a larger LaTeX file.
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

tex_summaries_combined: $(TEX_SUMMARIES_COMBINED)

$(TEX_SUMMARIES_COMBINED): $(TEX_SUMMARIES)
	@echo $(TEX_SUMMARIES) | \
		tr " " "\n" | \
		sed 's/^report\///' | \
		awk '{printf("\\input{%s}\n", $$1)}' | sort -n | \
		awk '{printf("%s\n\\clearpage\n", $$0)}' > $@

clean:
	rm -f $(CSV_LOGS) $(CSV_SUMMARIES) $(TEX_SUMMARIES) $(TEX_SUMMARIES_COMBINED)
