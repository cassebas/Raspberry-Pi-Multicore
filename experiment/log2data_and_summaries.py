import click
import click_log
import logging
from os.path import basename, isfile, isdir, join
import numpy as np
import pandas as pd
import re


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


def remove_quotes(quoted):
    if type(quoted) is str:
        quoted = re.sub(r'^\'', '', quoted)
        quoted = re.sub(r'\'$', '', quoted)
    return quoted


def export_dataframe(df, output_mode, axis0, axis1, output_directory):
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

            output_filename = 'cycles{}-{}-'.format(output_mode, label)
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
@click_log.simple_verbosity_option(logger)
def main(input_file, output_directory, output_mode):
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

    # Get the basename for the output files, a convention that is
    # used to link input log CSV files to output summary CSV files.
    # Pre condition for this to work: *all* log files must begin with /^log-/
    regex = re.compile('^log-(.*).csv$')
    m = regex.match(basename(input_file))
    if (m):
        logname = m.group(1)
    else:
        logname = 'default'
    logger.debug('Found logname {}.'.format(logname))

    # Construct a pivot table:
    #  - benchmarks/core will be indexed as columns,
    #  - cores, configuration, dassign, pattern will be the index
    # From this pivot table we can easily select the median/std cycles and
    # output them to specific CSV files for specific benchmarks/config/dassign.
    # These resulting CSV files are read from within LaTeX.
    #    (Note: 'cores' == nr of cores,  'core' == core number)
    if output_mode == 'data':
        df = df.set_index(keys=['label', 'cores', 'configuration', 'pattern'])
    elif output_mode == 'summary':
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
    for label in df.index.get_level_values(0):
        logger.debug('label={}'.format(label))

        cores_list = df.index.get_level_values(1)
        logger.debug('cores_list={}'.format(cores_list))
        for cores in set(cores_list):
            logger.debug('cores={}.'.format(cores))

            for config in set(df.index.get_level_values(2)):
                logger.debug('config={}.'.format(config))

                if output_mode != 'data':
                    axis0 = (label, cores, config, slice(None))
                    export_dataframe(df, output_mode, axis0, axis1,
                                     output_directory)
                else:  # output_mode == 'data':
                    for pattern in set(df.index.get_level_values(3)):
                        logger.debug('pattern={}'.format(pattern))
                        axis0 = (label, cores, config, pattern)
                        export_dataframe(df, output_mode, axis0, axis1,
                                         output_directory)


if __name__ == "__main__":
    main()
