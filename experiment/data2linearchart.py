import click
import click_log
import logging
from os.path import basename, isfile, isdir, join
# import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


benchmark_list = ['malardalen bsort100',
                  'malardalen edn',
                  'linear array access',
                  'random array access',
                  'random array write']


def remove_quotes(quoted):
    if type(quoted) is str:
        quoted = re.sub(r'^\'', '', quoted)
        quoted = re.sub(r'\'$', '', quoted)
    return quoted


@click.command()
@click.option('--input-file',
              required=True,
              help='Path and filename of the input file.')
@click.option('--output-directory',
              default='report/img',
              help='Path of the output directory.')
@click.option('--maximum-observations',
              default=250,
              help='Maximum number of observations to plot.')
@click.option('--movingaverage-window',
              default=0,
              help='Size of the moving average window, 0=no moving average (default)')
@click_log.simple_verbosity_option(logger)
def main(input_file, output_directory, maximum_observations,
         movingaverage_window):

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

    win = movingaverage_window
    if win < 0:
        logger.error('Moving average window is negative ' +
                     '({}), it must be 0 or greater.'.format(win))
        logger.info('Exiting program due to error.')
        exit(1)

    logger.info('Processing input file {}.'.format(input_file))
    df = pd.read_csv(input_file, sep=' ')

    # Get the basename for the output files, a convention that is
    # used to link input log CSV files to output summary CSV files.
    # Pre condition for this to work: *all* log files must begin with /^log-/
    regex = re.compile('^cyclesdata-(.*)-.*.csv$')
    m = regex.match(basename(input_file))
    if (m):
        logname = m.group(1)
    else:
        logname = 'default'
    logger.debug('Found logname {}.'.format(logname))

    # Find out number of cores
    cores_list = df.cores.unique()
    if len(cores_list) != 1:
        logger.warning('The uniqueness of the number of cores is not 1!')
    cores = cores_list[0]
    logger.debug('cores={}'.format(cores))
    rowcount = maximum_observations * cores
    df = df.iloc[:rowcount, ]

    configuration_list = df.configuration.unique()
    if len(configuration_list) != 1:
        logger.warning('The uniqueness of the number of configurations ' +
                       ' is not 1!')
    config = remove_quotes(configuration_list[0])
    # assertion: number of cores must equal the length of the config string
    if len(config) != cores:
        logger.warning('Length of config string is not equal number of cores!')
    logger.debug('config={}'.format(config))

    dassign_list = df.dassign.unique()
    if len(dassign_list) != 1:
        logger.warning('The uniqueness of the dassign column values is not 1!')
    dassign = remove_quotes(dassign_list[0])
    logger.debug('dassign={}'.format(dassign))

    pattern_list = df.pattern.unique()
    if len(pattern_list) != 1:
        logger.warning('The uniqueness of the pattern column values is not 1!')
    pattern = remove_quotes(pattern_list[0])
    logger.debug('pattern={}'.format(pattern))

    benchmarks = [benchmark_list[int(b)-1] for b in config]
    logger.debug('benchmarks={}'.format(benchmarks))

    plt.figure(figsize=[10, 5])
    plt.grid(True)
    for corenum in range(cores):
        dfcore = df.loc[df['core'] == corenum]
        dfcore = dfcore.set_index(['iteration'])
        if win > 0:
            dfcore['mav'] = dfcore.loc[:, 'cycles']
            dfcore['mav'] = dfcore['mav'].rolling(window=win).mean()
            label = 'moving average (win={}) '.format(win)
            field2plot = 'mav'
        else:
            label = ''
            field2plot = 'cycles'
        label += 'core{} - {}'.format(corenum, benchmarks[corenum])
        plt.xlabel('Iteration')
        plt.ylabel('Number of cycles')
        plt.plot(dfcore[field2plot], label=label)
    plt.legend(loc=1)

    output_filename = 'cycles{}-{}-'.format('data', logname)
    output_filename += '{}core-config{}-'.format(cores, config)
    output_filename += '{}{}-'.format('dassign', dassign)
    output_filename += '{}{}.png'.format('pattern', pattern)
    logger.debug('output_filename={}'.format(output_filename))
    outfile = join(output_directory, output_filename)
    plt.savefig(outfile)


if __name__ == "__main__":
    main()
