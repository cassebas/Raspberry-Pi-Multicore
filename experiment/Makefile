# Convert log files to CSV with observations, 1 line per core
LOG_DIR=output
LOG_FILES=$(shell find $(LOG_DIR) -name "*.log")
CSV_FILES=$(patsubst %.log,%.csv,$(LOG_FILES))
DATA_DIR=report/data

CSV_SUMMARIES=$(shell find $(DATA_DIR) -name "*.csv")
TEX_SUMMARIES=$(patsubst %.csv,%.tex,$(CSV_SUMMARIES))

.phony: run clean

define CSV2SUMMARY
	python csv2summary.py --input-file=$(1) --output-directory=$(DATA_DIR);
endef

run: $(CSV_FILES) $(TEX_SUMMARIES)
	$(foreach csv_file,$(CSV_FILES),$(call CSV2SUMMARY,$(csv_file)))

$(CSV_FILES): $(LOG_FILES)
	$(eval LOG := $(patsubst %.csv,%.log,$@))
	awk -f log2csv.awk $(LOG) > $@

$(TEX_SUMMARIES): $(CSV_SUMMARIES)
	$(eval CSV := $(patsubst %.csv,%.tex,$@))
	$(eval CFG := `echo $(CSV)|sed 's/^.*config\([0-9]*\).*/\1/'`)
	$(eval DT := `echo $(CSV)|sed 's/^.*config[0-9]*-\([a-z]*\).*/\1/'`)
	@echo "config is "$(CFG)
	@echo "csv is "$(CSV)
	@echo "dtype is "$(DT)
	m4 -Dfilename=$(CSV) -Dconfig=$(CFG) -Ddtype=$(DT) maketex-cyclesummaries.m4 > $@

clean:
	rm -f $(LOG_DIR)/*.csv
