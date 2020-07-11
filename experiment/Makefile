# Convert log files to CSV with observations, 1 line per core
LOG_DIR=output
TXT_LOGS=$(shell find $(LOG_DIR) -name "*.log")
CSV_LOGS_CYCLES=$(patsubst %.log,%-cycles.csv,$(TXT_LOGS))
CSV_LOGS_EVENTS=$(patsubst %.log,%-events.csv,$(TXT_LOGS))
DATA_DIR=report/data
IMG_DIR=report/img

CSV_SUMMARIES=$(shell find $(DATA_DIR) -name "cyclessummary-*.csv")
TEX_SUMMARIES=$(patsubst %.csv,%.tex,$(CSV_SUMMARIES))
TEX_SUMMARIES_COMBINED=report/input-figures.tex

CSV_DATA_CYCLES=$(shell find $(DATA_DIR) -name "cyclesdata-*.csv")
CSV_DATA_EVENTS=$(shell find $(DATA_DIR) -name "eventsdata-*.csv")
PNG_DATA=$(patsubst %.csv,%.png,$(CSV_DATA_CYCLES))
PNG_DATA_CLEAN=$(shell find $(IMG_DIR) -name "cyclesdata-*.png")

.phony: all csv_summaries csv_data tex_summaries_combined png_data clean

# Macro that will generate all summary data files in CSV format
define LOG2_SUMMARIES
	python log2data_and_summaries.py --input-file=$(1) --output-directory=$(DATA_DIR) --output-mode=summary;
endef

# Macro that will generate all linear chart data files in CSV format
define LOG2_DATA_CYCLES
	python log2data_and_summaries.py --input-file=$(1) --output-directory=$(DATA_DIR) --output-mode=data --metric=cycles;
endef
define LOG2_DATA_EVENTS
	python log2data_and_summaries.py --input-file=$(1) --output-directory=$(DATA_DIR) --output-mode=data --metric=events;
endef

# Recursive call to make, to make sure that csv_summaries is fully
# completed before tex_summaries_combined is executed.
all: csv_summaries csv_data_cycles csv_data_events
	make tex_summaries_combined png_data

# $(CSV_SUMMARIES) cannot be a target, because the exact .csv files with
# summary data aren't known beforehand. The python scripts extracts them
# from the data contained in the .csv log files.
csv_summaries: $(CSV_LOGS_CYCLES)
	$(foreach csv_file,$(CSV_LOGS_CYCLES),$(call LOG2_SUMMARIES,$(csv_file)))

# $(CSV_DATA_CYCLES) cannot be a target, because the exact .csv files with
# the data aren't known beforehand. The python scripts extracts them
# from the data contained in the .csv log files.
csv_data_cycles: $(CSV_LOGS_CYCLES)
	$(foreach csv_file,$(CSV_LOGS_CYCLES),$(call LOG2_DATA_CYCLES,$(csv_file)))
# $(CSV_DATA_EVENTS) cannot be a target, because the exact .csv files with
# the data aren't known beforehand. The python scripts extracts them
# from the data contained in the .csv log files.
csv_data_events: $(CSV_LOGS_EVENTS)
	$(foreach csv_file,$(CSV_LOGS_EVENTS),$(call LOG2_DATA_EVENTS,$(csv_file)))

# Implicit target: simple 1 to 1 translation for -cycles.log to .csv using AWK
$(CSV_LOGS_CYCLES): $(TXT_LOGS)
	$(eval LOG_CYCLES := $(patsubst %-cycles.csv,%.log,$@))
	awk -f log2csv-cyclecount.awk $(LOG_CYCLES) > $@

# Implicit target: simple 1 to 1 translation for -events.log to .csv using AWK
$(CSV_LOGS_EVENTS): $(TXT_LOGS)
	$(eval LOG_EVENTS := $(patsubst %-events.csv,%.log,$@))
	awk -f log2csv-eventcount.awk $(LOG_EVENTS) > $@

# This can be an implicit target, because all CSV_SUMMARIES are known by now
# For each *.csv summary, a .tex file is generated with a pgfplot figure, that
# is to be included into a larger LaTeX file.
$(TEX_SUMMARIES): $(CSV_SUMMARIES)
	$(eval TEX := $(patsubst %.csv,%.tex,$@))
	$(eval CSV := $(patsubst %.tex,%.csv,$(TEX)))
	$(eval INPUT := `echo $(CSV)|sed 's/^report\///'`)
	$(eval LABEL := `echo $(TEX)|sed 's/^.*cyclessummary-\([^-]*\)-.*/\1/'`)
	$(eval CFG_S := `echo $(TEX)|sed 's/^.*configseries\([0-9]*\).*/\1/'`)
	$(eval CFG_B := `echo $(TEX)|sed 's/^.*configbench\([0-9]*\).*/\1/'`)
	@echo "csv is "$(CSV)
	@echo "tex is "$(TEX)
	@echo "label is "$(LABEL)
	@echo "config_series is "$(CFG_S)
	@echo "config_bench is "$(CFG_B)
	@echo "inputfile is "$(INPUT)
	m4 -Dfilename=$(INPUT) \
		-Dconfig_series=$(CFG_S) \
		-Dconfig_benchmarks=$(CFG_B) \
		-Dlabel=$(LABEL) maketex-cyclesummaries.m4 > $@

tex_summaries_combined: $(TEX_SUMMARIES_COMBINED)

$(TEX_SUMMARIES_COMBINED): $(TEX_SUMMARIES)
	@echo $(TEX_SUMMARIES) | \
		tr " " "\n" | \
		sed 's/^report\///' | \
		awk '{printf("\\input{%s}\n", $$1)}' | sort -n | \
		awk '{printf("%s\n\\clearpage\n", $$0)}' > $@

png_data: $(PNG_DATA)

# This can be an implicit target, because all CSV_SUMMARIES are known by now
# For each *.csv summary, a .tex file is generated with a pgfplot figure, that
# is to be included into a larger LaTeX file.
$(PNG_DATA): $(CSV_DATA_CYCLES)
	$(eval CSV := $(patsubst %.png,%.csv,$@))
	python data2linearchart.py --input-file=$(CSV) --output-directory=$(IMG_DIR) --maximum-observations=250 --movingaverage-window=0 --process-events=True

clean:
	rm -f $(CSV_CYCLE_LOGS) $(CSV_EVENT_LOGS) $(CSV_DATA_CYCLES) $(CSV_DATA_EVENTS) $(CSV_SUMMARIES) $(TEX_SUMMARIES) $(TEX_SUMMARIES_COMBINED) $(PNG_DATA_CLEAN)
