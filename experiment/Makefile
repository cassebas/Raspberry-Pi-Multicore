# Convert log files to CSV with observations, 1 line per core
LOG_DIR=output
LOG_FILES=$(shell find $(LOG_DIR) -name "*.log")
CSV_FILES=$(patsubst %.log,%.csv,$(LOG_FILES))
DATA_DIR=report/data

.phony: run clean

define CSV2SUMMARY
	python csv2summary.py --input-file=$(1) --output-directory=$(DATA_DIR);
endef

run: $(CSV_FILES)
	$(foreach csv_file,$(CSV_FILES),$(call CSV2SUMMARY,$(csv_file)))

$(CSV_FILES): $(LOG_FILES)
	$(eval LOG := $(patsubst %.csv,%.log,$@))
	awk -f log2csv.awk $(LOG) > $@

clean:
	rm -f $(LOG_DIR)/*.csv
