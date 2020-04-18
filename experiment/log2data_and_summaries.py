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


def export_dataframe(df, output_mode, axis0, axis1, data_type,
                     logname, output_directory):
    # assert the data_type is either dassign or pattern
    if data_type is not None:
        if data_type != 'dassign' and data_type != 'pattern':
            logger.warning('Illegal datatype {} found.'.format(data_type))

    # axis0 is a tuple containing:
    #   output_mode==summary, data_type==dassign
    #     (cores, config, dassign, slice(None))
    #   output_mode==summary, data_type==pattern
    #     (cores, config, slice(None), pattern)
    #   output_mode==data
    #     (cores, config, dassign, pattern)
    (cores, config, dassign, pattern) = axis0

    try:
        df_exp = df.loc[axis0, axis1]
        df_exp = df_exp.dropna(axis=0, how='all')
        df_exp = df_exp.dropna(axis=1, how='all')
        if len(df_exp.index) > 0:
            if output_mode == 'summary':
                df_exp.columns = df_exp.columns.to_series().str.join('-')

            config = remove_quotes(config)
            dassign = remove_quotes(dassign)
            pattern = remove_quotes(pattern)

            output_filename = 'cycles{}-{}-'.format(output_mode, logname)
            output_filename += '{}core-config{}-'.format(cores, config)

            if output_mode == 'data':
                output_filename += '{}{}-'.format('dassign', dassign)
                output_filename += '{}{}.csv'.format('pattern', pattern)
            else:
                if data_type == 'dassign':
                    output_filename += '{}{}.csv'.format(data_type, dassign)
                else:
                    output_filename += '{}{}.csv'.format(data_type, pattern)
            logger.debug('output_filename={}'.format(output_filename))

            outfile = join(output_directory, output_filename)
            df_exp.to_csv(outfile, index=True, sep=' ')
    except KeyError:
        logger.warning('KeyError => cores={} '.format(cores) +
                       ' config={} dassign={}'.format(config, dassign))


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
        df = df.set_index(keys=['cores', 'configuration', 'dassign', 'pattern'])
    elif output_mode == 'summary':
        df = pd.pivot_table(df,
                            index=['cores', 'configuration', 'dassign',
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
    #  - level 0: number of cores
    #  - level 1: configuration string
    #  - level 2: data assignment string
    #  - level 3: alignment pattern string
    cores_list = df.index.get_level_values(0)
    core_min = cores_list[0]
    core_max = cores_list[-1]
    logger.debug('cores_list={}'.format(cores_list))

    for cores in set(cores_list):
        for core_number in range(core_min, core_max+1):
            cidx = ['core'+str(i) for i in range(core_number)]
        logger.debug('cidx={}.'.format(cidx))

        if output_mode == 'data':
            axis1 = (slice(None))
        else:
            axis1 = (slice(None), slice(None), cidx)

        # df_sub index levels:
        #  - level 0: configuration string
        #  - level 1: data assignment string
        #  - level 2: alignment pattern string
        df_sub = df.loc[cores]

        for config in set(df_sub.index.get_level_values(0)):
            logger.debug('config={}.'.format(config))

            if output_mode != 'data':
                for dassign in set(df_sub.index.get_level_values(1)):
                    logger.debug('dassign={}.'.format(dassign))
                    axis0 = (cores, config, dassign, slice(None))
                    export_dataframe(df, output_mode, axis0, axis1,
                                     'dassign', logname, output_directory)

                for pattern in set(df_sub.index.get_level_values(2)):
                    logger.debug('pattern={}.'.format(pattern))
                    axis0 = (cores, config, slice(None), pattern)
                    export_dataframe(df, output_mode, axis0, axis1,
                                     'pattern', logname, output_directory)

            else:  # output_mode == 'data':
                for dassign in set(df_sub.index.get_level_values(1)):
                    logger.debug('dassign={}.'.format(dassign))
                    for pattern in set(df_sub.index.get_level_values(2)):
                        logger.debug('pattern={}'.format(pattern))
                        axis0 = (cores, config, dassign, pattern)
                        export_dataframe(df, output_mode, axis0, axis1,
                                         None, logname, output_directory)


if __name__ == "__main__":
    main()
