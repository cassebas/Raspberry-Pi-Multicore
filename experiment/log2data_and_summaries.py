import sys
import click
import click_log
import logging
from os.path import isfile, isdir, join
import numpy as np
import pandas as pd
import re


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


pmu_event_names = {
    3: 'L1D_CACHE_REFILL',
    4: 'L1D_CACHE',
    16: 'BR_MIS_PRED',
    18: 'BR_PRED',
    19: 'MEM_ACCESS',
    21: 'L1D_CACHE_WB',
    22: 'L2D_CACHE',
    23: 'L2D_CACHE_REFILL',
    24: 'L2D_CACHE_WB',
    25: 'BUS_ACCESS',
}


def remove_quotes(quoted):
    if type(quoted) is str:
        quoted = re.sub(r'^\'', '', quoted)
        quoted = re.sub(r'\'$', '', quoted)
    return quoted


def export_dataframe(df, output_mode, metric, axis0, axis1, output_directory):
    # axis0 is a tuple containing:
    #   output_mode==summary
    #     (label, cores, config, slice(None))
    #   output_mode==data
    #     (label, cores, config, pattern)
    (label, cores, config, pattern) = axis0

    try:
        df_exp = df.loc[axis0, axis1]
        df_exp = df_exp.dropna(axis=0, how='all')
        df_exp = df_exp.dropna(axis=1, how='all')
        if len(df_exp.index) > 0:
            if output_mode == 'summary':
                df_exp.columns = df_exp.columns.to_series().str.join('-')

            config = remove_quotes(config)
            pattern = remove_quotes(pattern)

            output_filename = '{}{}-{}-'.format(metric, output_mode, label)
            output_filename += '{}core-config{}'.format(cores, config)

            if output_mode == 'data':
                output_filename += '-{}{}.csv'.format('pattern', pattern)
            else:
                output_filename += '.csv'
            logger.debug('output_filename={}'.format(output_filename))

            outfile = join(output_directory, output_filename)
            df_exp.to_csv(outfile, index=True, sep=' ')
        else:
            logger.warning('Trying to export an empty dataframe.')
    except KeyError:
        logger.warning('KeyError => label={} '.format(label) +
                       'cores={} config={}'.format(cores, config))


@click.command()
@click.option('--input-file',
              required=True,
              help='Path and filename of the input file.')
@click.option('--output-directory',
              default='report/data',
              help='Path of the output directory.')
@click.option('--output-mode',
              default='data',
              help='Mode of the output, either data or summary.')
@click.option('--metric',
              default='cycles',
              help='Metric contained in the logs, either cycles or events. ' +
                   'The metric argument pertains to data output mode only.')
@click_log.simple_verbosity_option(logger)
def main(input_file, output_directory, output_mode, metric):
    if not isfile(input_file):
        logger.error('Input file {}'.format(input_file) +
                     ' does not exist!')
        logger.info('Exiting program due to error.')
        exit(1)

    if not isdir(output_directory):
        logger.error('Output directory {}'.format(output_directory) +
                     ' does not exist!')
        logger.info('Exiting program due to error.')
        exit(1)

    logger.info('Processing input file {}.'.format(input_file))
    df = pd.read_csv(input_file)

    # Construct a pivot table:
    #  - benchmarks/core will be indexed as columns,
    #  - cores, configuration, dassign, pattern will be the index
    # From this pivot table we can easily select the median/std cycles and
    # output them to specific CSV files for specific benchmarks/config/dassign.
    # These resulting CSV files are read from within LaTeX.
    #    (Note: 'cores' == nr of cores,  'core' == core number)
    if output_mode == 'data':
        if metric != 'cycles' and metric != 'events':
            logger.error('Illegal metric for ' +
                         'output mode {}'.format(output_mode))
            logger.info('Exiting program due to error.')
            exit(1)

        df = df.set_index(keys=['label', 'cores', 'configuration', 'pattern'])
    elif output_mode == 'summary':
        if metric == 'events':
            logger.error('Illegal metric for ' +
                         'output mode {}'.format(output_mode))
            logger.info('Exiting program due to error.')
            exit(1)

        df = pd.pivot_table(df,
                            index=['label', 'cores', 'configuration',
                                   'pattern'],
                            columns=['benchmark', 'core'],
                            values='cycles',
                            aggfunc={'cycles': [np.median, np.std]})
        df = df.rename(columns={0: 'core0',
                                1: 'core1',
                                2: 'core2',
                                3: 'core3'})
    else:
        logger.error('Illegal output mode "{}"'.format(output_mode) +
                     ', output mode must be either data or summary.')
        logger.info('Exiting program due to error.')
        exit(1)

    df.sort_index(inplace=True)

    # Now output a series of CVS files that contain the summaries
    # The index levels of the df dataframe are:
    #  - level 0: label of experiment
    #  - level 1: number of cores
    #  - level 2: configuration string
    #  - level 3: alignment pattern string

    axis1 = (slice(None))
    for label in set(df.index.get_level_values(0)):
        logger.debug('label={}'.format(label))
        dflabel = df.loc[label, :]
        cores_list = dflabel.index.get_level_values(0)
        logger.debug('cores_list={}'.format(cores_list))

        for cores in set(cores_list):
            logger.debug('cores={}.'.format(cores))
            dfcore = dflabel.loc[cores, :]
            config_list = dfcore.index.get_level_values(0)
            logger.debug('config_list={}'.format(config_list))

            for config in set(config_list):
                logger.debug('config={}.'.format(config))

                if output_mode != 'data':
                    axis0 = (label, cores, config, slice(None))
                    export_dataframe(df, output_mode, metric, axis0, axis1,
                                     output_directory)

                else:  # output_mode == 'data':
                    dfconfig = dfcore.loc[config, :]
                    pattern_list = dfconfig.index.get_level_values(0)
                    logger.debug('pattern_list={}'.format(pattern_list))

                    for pattern in set(pattern_list):
                        logger.debug('pattern={}'.format(pattern))
                        axis0 = (label, cores, config, pattern)
                        export_dataframe(df, output_mode, metric, axis0, axis1,
                                         output_directory)


if __name__ == "__main__":
    main()
