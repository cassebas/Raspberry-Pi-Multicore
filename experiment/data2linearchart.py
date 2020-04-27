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
                  'linear array write',
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
              help='Size of the moving average window, 0=no moving average ' +
                   ' (default)')
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

    # Get experiment label
    experiment_labels = df.label.unique()
    if len(experiment_labels) != 1:
        logger.warning('The uniqueness of the label is not 1!')
    exp_label = experiment_labels[0]
    logger.debug('experiment label={}'.format(exp_label))

    # Find out number of cores
    cores_list = df.cores.unique()
    if len(cores_list) != 1:
        logger.warning('The uniqueness of the number of cores is not 1!')
    cores = cores_list[0]
    logger.debug('cores={}'.format(cores))
    rowcount = maximum_observations * cores
    df = df.iloc[:rowcount, ]

    # Get the event types (now hardcoded 2 events present in the data)
    event1_list = df.event1_type.unique()
    if len(event1_list) != 1:
        logger.warning('The uniqueness of the event type 1 is not 1!')
    event1_type = event1_list[0]
    logger.debug('event1_type={}'.format(event1_type))

    # Get the event types (now hardcoded 2 events present in the data)
    event2_list = df.event2_type.unique()
    if len(event2_list) != 1:
        logger.warning('The uniqueness of the event type 2 is not 1!')
    event2_type = event2_list[0]
    logger.debug('event2_type={}'.format(event2_type))

    configuration_list = df.configuration.unique()
    if len(configuration_list) != 1:
        logger.warning('The uniqueness of the number of configurations ' +
                       ' is not 1!')
    config = remove_quotes(configuration_list[0])
    # assertion: number of cores must equal the length of the config string
    if len(config) != cores:
        logger.warning('Length of config string is not equal number of cores!')
    logger.debug('config={}'.format(config))

    pattern_list = df.pattern.unique()
    if len(pattern_list) != 1:
        logger.warning('The uniqueness of the pattern column values is not 1!')
    pattern = remove_quotes(pattern_list[0])
    logger.debug('pattern={}'.format(pattern))

    benchmarks = [benchmark_list[int(b)-1] for b in config]
    logger.debug('benchmarks={}'.format(benchmarks))

    fig, ax = plt.subplots(cores, 1, sharey=True, figsize=(20,15))
    left = 0.145  # the left side of the subplots of the figure
    right = 0.92  # the right side of the subplots of the figure
    bottom = 0.15 # the bottom of the subplots of the figure
    top = 0.9     # the top of the subplots of the figure
    wspace = 0.3  # the amount of width reserved for space between subplots,
                  # expressed as a fraction of the average axis width
    hspace = 0.5  # the amount of height reserved for space between subplots,
                  # expressed as a fraction of the average axis height
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top,
                        wspace=wspace, hspace=hspace)
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
        ax[corenum].set_ylabel('Cycles')
        ax[corenum].plot(dfcore.index, dfcore[field2plot], label=label,
                         color='blue')
        ax[corenum].legend(loc=1)
        ax[corenum].grid(True)
        # plot the two event types that were also measured
        ax2 = ax[corenum].twinx()
        ax2.plot(dfcore.index, dfcore['event1_value'], color='green',
                 label=event1_type)
        ax2.set_ylabel(event1_type)
        ax2.legend(loc=0)
        ax2.plot(dfcore.index, dfcore['event2_value'], color='red',
                 label=event2_type)
        ax2.set_ylabel(event2_type)
        ax2.legend(loc=0)
    ax[0].set_title(exp_label)
    ax[cores-1].set_xlabel('Iteration')

    output_filename = 'cycles{}-{}-'.format('data', logname)
    output_filename += '{}core-config{}-'.format(cores, config)
    output_filename += '{}{}.png'.format('pattern', pattern)
    logger.debug('output_filename={}'.format(output_filename))
    outfile = join(output_directory, output_filename)
    plt.savefig(outfile)


if __name__ == "__main__":
    main()
