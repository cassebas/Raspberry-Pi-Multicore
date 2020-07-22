import click
import click_log
import logging
import glob
import os
# from os.path import basename, isfile, join
from os.path import isfile, join
import subprocess
from subprocess import CalledProcessError
import numpy as np
import pandas as pd
import re
import time
from enum import Enum
# import signal
from threading import Thread
import serial
# from warnings import warn
import sys


benchmark_list = [
    ['linear array access',
     'linear array write',
     'random array access',
     'random array write'],
    ['malardalen bsort100',
     'malardalen edn',
     'malardalen matmult'],
    ['sd-vbs disparity']]


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


def remove_quotes(string):
    string = re.sub(r'^\'', '', string)
    string = re.sub(r'\'$', '', string)
    return string


class Fields(Enum):
    NUMBER = 1
    CONFIG_SERIES = 2
    CONFIG_BENCH = 3
    DISABLE_CACHE = 4
    ENABLE_MMU = 5
    ENABLE_SCREEN = 6
    NO_CACHE_MGMT = 7
    SB_DATASIZE = 8
    EXP_LABEL = 9
    PMU_CORE0 = 10
    PMU_CORE1 = 11
    PMU_CORE2 = 12
    PMU_CORE3 = 13
    DISP_INPUT = 14
    BSORT_INPUT = 15
    MATMULT_INPUT = 16
    TICK_RATE_HZ = 17


flds = {
    Fields.NUMBER: 'experiment number',
    Fields.CONFIG_SERIES: 'benchmark series',
    Fields.CONFIG_BENCH: 'benchmark configuration',
    Fields.DISABLE_CACHE: 'disable cache',  # not implemented for now
    Fields.ENABLE_MMU: 'enable mmu',
    Fields.ENABLE_SCREEN: 'enable screen',
    Fields.NO_CACHE_MGMT: 'no cache management',
    Fields.SB_DATASIZE: 'synbench datasize',
    Fields.EXP_LABEL: 'experiment label',
    Fields.PMU_CORE0: 'pmu core 0',
    Fields.PMU_CORE1: 'pmu core 1',
    Fields.PMU_CORE2: 'pmu core 2',
    Fields.PMU_CORE3: 'pmu core 3',
    Fields.DISP_INPUT: 'disparity inputsize',
    Fields.BSORT_INPUT: 'bsort inputsize',
    Fields.MATMULT_INPUT: 'matmult inputsize',
}


def get_experiment_labels(input_file):
    df = pd.read_excel(input_file)

    # first pass, extract all 1-core experiments that are baseline
    # to the other experiments
    exp_keys = {}
    exp_mapping = {}
    for idx, row in df.iterrows():
        exp_nr = row[flds[Fields.NUMBER]]
        config_series = row[flds[Fields.CONFIG_SERIES]]
        config_bench = row[flds[Fields.CONFIG_BENCH]]

        # remove quotes from strings (if present)
        config_series = remove_quotes(config_series)
        config_bench = remove_quotes(config_bench)

        if len(config_series) != len(config_bench):
            # Illegal combination of lengths config_series and config_bench,
            # they must be of equal length
            logger.warning('Illegal lengths of series and benchmarks ' +
                           'configuration!')
            logger.warning('Skipping experiment number {}'.format(exp_nr))
            continue

        if len(config_series) == 1:
            # This is a 1-core experiment, remember the experiment by making
            # a hash key that contains the configuration and the parameters
            # of the experiment.
            # This key will be used for matching against the multiple core
            # experiments with the same parameters.
            exp_key = str(config_series) + str(config_bench) + '_'
            exp_key += str(row[flds[Fields.ENABLE_MMU]]) + '_'
            exp_key += str(row[flds[Fields.ENABLE_SCREEN]]) + '_'
            exp_key += str(row[flds[Fields.NO_CACHE_MGMT]]) + '_'
            exp_key += str(row[flds[Fields.SB_DATASIZE]]) + '_'
            exp_key += str(row[flds[Fields.DISP_INPUT]]) + '_'
            exp_key += str(row[flds[Fields.BSORT_INPUT]]) + '_'
            exp_key += str(row[flds[Fields.MATMULT_INPUT]])
            exp_keys[exp_key] = row[flds[Fields.EXP_LABEL]]

    # second pass, extract all n-core experiments that have co-runners
    for idx, row in df.iterrows():
        config_series = row[flds[Fields.CONFIG_SERIES]]
        config_bench = row[flds[Fields.CONFIG_BENCH]]

        # remove quotes from strings (if present)
        config_series = remove_quotes(config_series)
        config_bench = remove_quotes(config_bench)

        # Construct the hash key for matching against the 1-core
        # experiment with the same parameters.
        # Note that the 1-core experiment will also be matched to itself.
        exp_key = str(config_series[0]) + str(config_bench[0]) + '_'
        exp_key += str(row[flds[Fields.ENABLE_MMU]]) + '_'
        exp_key += str(row[flds[Fields.ENABLE_SCREEN]]) + '_'
        exp_key += str(row[flds[Fields.NO_CACHE_MGMT]]) + '_'
        exp_key += str(row[flds[Fields.SB_DATASIZE]]) + '_'
        exp_key += str(row[flds[Fields.DISP_INPUT]]) + '_'
        exp_key += str(row[flds[Fields.BSORT_INPUT]]) + '_'
        exp_key += str(row[flds[Fields.MATMULT_INPUT]])

        label = row[flds[Fields.EXP_LABEL]]
        if exp_key in exp_keys:
            exp_mapping[label] = exp_keys[exp_key]

    exp_list = []
    for key, val in exp_mapping.items():
        exp_list.append([key, val])
    df_mapping = pd.DataFrame.from_records(exp_list,
                                           columns=['label',
                                                    'label1core'])
    return df_mapping


def get_experiment_data(csv_dir):
    df = pd.DataFrame()
    dfs = pd.DataFrame()
    infiles = glob.glob(join(csv_dir, '*-cycles.csv'))
    for f in infiles:
        df = pd.read_csv(f)
        df_pivot = pd.pivot_table(df,
                                  index=['label', 'cores',
                                         'config_series', 'config_benchmarks',
                                         'pattern'],
                                  columns=['benchmark', 'core'],
                                  values='cycles',
                                  aggfunc={'cycles': [np.median,
                                                      np.std,
                                                      np.max]})
        df_pivot = df_pivot.rename(columns={0: 'core0',
                                            1: 'core1',
                                            2: 'core2',
                                            3: 'core3'})
        dfs = pd.concat([dfs, df_pivot])
    dfs.sort_index(inplace=True)
    return dfs


def get_experiment_results(exp_labels, exp_data):
    exp_results = pd.DataFrame()

    # Extend the experiments dataframe with result data
    for idx, row in exp_labels.iterrows():
        label = row['label']
        try:
            df_tmp = exp_data.loc[label,
                                  (slice(None), slice(None), ['core0'])]
            if len(df_tmp.index) > 0:
                cores = df_tmp.index.get_level_values(0)[0]
                config_series = df_tmp.index.get_level_values(1)[0]
                config_bench = df_tmp.index.get_level_values(2)[0]
                # remove quotes from strings (if present)
                config_series = remove_quotes(config_series)
                config_bench = remove_quotes(config_bench)

                benchmarks = [benchmark_list[int(tup[0])-1][int(tup[1])-1]
                              for tup in zip(config_series, config_bench)]
                benchmark = benchmarks[0]

                # strip whitespace from benchmark name
                benchmark = re.sub(r' ', '', benchmark)
                # strip '-' from benchmark name
                benchmark = re.sub(r'-', '', benchmark)
                pattern_list = df_tmp.index.get_level_values(3)
                logger.debug('pattern list is {}'.format(pattern_list))

                for pattern in pattern_list:
                    df_tmp_pattern = df_tmp.loc[(slice(None),
                                                 slice(None),
                                                 slice(None),
                                                 pattern),
                                                (slice(None),
                                                 [benchmark],
                                                 ['core0'])]

                    # dftmp now contains one row, three cols (max, median, std)
                    wcet = df_tmp_pattern.iloc[0, 0]
                    median = df_tmp_pattern.iloc[0, 1]
                    std = df_tmp_pattern.iloc[0, 2]
                    if median != 0:
                        wcet_median_factor = wcet / median
                    else:
                        wcet_median_factor = None

                    label1core = row['label1core']
                    df1_tmp = exp_data.loc[label1core,
                                           (slice(None),
                                            [benchmark],
                                            ['core0'])]
                    if len(df1_tmp.index) > 0:
                        # dftmp now contains one row, three cols (max, median, std)
                        wcet1 = df1_tmp.iloc[0, 0]
                        median1 = df1_tmp.iloc[0, 1]
                        std1 = df1_tmp.iloc[0, 2]

                        if wcet1 != 0:
                            slowdown_factor = wcet / wcet1
                        else:
                            slowdown_factor = None

                        if median1 != 0:
                            median_factor = median / median1
                        else:
                            median_factor = None

                        if std1 != 0:
                            std_factor = std / std1
                        else:
                            std_factor = None

                        logger.debug('Label:{} '.format(label) +
                                     'pattern:{} '.format(pattern) +
                                     'Slowdown ' +
                                     'factor:{}'.format(wcet/wcet1))
                        ps = pd.Series({'label': label,
                                        'label1core': label1core,
                                        'cores': cores,
                                        'benchmark': benchmark,
                                        'pattern': pattern,
                                        'wcet': wcet,
                                        'wcet_median_factor': wcet_median_factor,
                                        'slowdown_factor': slowdown_factor,
                                        'median': median,
                                        'median_factor': median_factor,
                                        'stdev': std,
                                        'stdev_factor': std_factor})
                        exp_results = exp_results.append(ps, ignore_index=True)
        except KeyError:
            logger.debug('Caught KeyError for label {}'.format(label))

    return exp_results


@click.command()
@click.option('--input-file',
              required=True,
              help=('Path and filename of the input Excel file containing' +
                    ' the experiments.'))
@click.option('--output-file',
              required=True,
              help='Path and filename of the output file.')
@click.option('--csv-dir',
              default='output',
              help='Path of the directory where the CSV logs are stored.')
@click_log.simple_verbosity_option(logger)
def main(input_file, output_file, csv_dir):
    if not isfile(input_file):
        logger.error('Error: input file {} '.format(input_file) +
                     'does not exist!')
        exit(1)
    if isfile(output_file):
        logger.error('Error: output file {} '.format(output_file) +
                     'already exists!')
        exit(1)

    # First get all labels of the experiments, mapped to their
    # corresponding single run (no co-runners) experiments.
    logger.info('Reading experiment labels from excel file ' +
                ' "{}".'.format(input_file))
    exp_labels = get_experiment_labels(input_file)

    logger.info('Reading experiment data from CSV files found ' +
                'in directory "{}".'.format(csv_dir))
    exp_data = get_experiment_data(csv_dir)

    logger.info('Combining label mappings with experiment data...')
    exp_results = get_experiment_results(exp_labels, exp_data)
    logger.info('Writing resulting slowdown factors to CSV ' +
                'output file "{}".'.format(output_file))
    exp_results.to_csv(output_file, index=False, sep=' ')


if __name__ == "__main__":
    main()
