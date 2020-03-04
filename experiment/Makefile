# Convert log files to CSV with observations, 1 line per core
LOG_DIR=output
LOG_FILES=$(shell find $(LOG_DIR) -name "*.log")
CSV_FILES=$(patsubst %.log,%.csv,$(LOG_FILES))
DATA_DIR=report/data

.phony: run clean

run: $(CSV_FILES)
	python csv2summary.py --input-directory=$(LOG_DIR) --output-directory=$(DATA_DIR)

$(CSV_FILES): $(LOG_FILES)
	$(eval LOG := $(patsubst %.csv,%.log,$@))
	awk -f log2csv.awk $(LOG) > $@

clean:
	rm -f $(LOG_DIR)/*.csv
