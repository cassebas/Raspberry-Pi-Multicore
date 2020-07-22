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


benchmark_list = [
    ['linear array access',
     'linear array write',
     'random array access',
     'random array write'],
    ['malardalen bsort100',
     'malardalen edn',
     'malardalen matmult'],
    ['sd-vbs disparity']]


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


def event_number2name(number):
    if number in pmu_event_names.keys():
        return pmu_event_names[number]
    else:
        return ""


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
@click.option('--process-events',
              default=True,
              help='Process the experiments\' corresponding events data file.')
@click_log.simple_verbosity_option(logger)
def main(input_file, output_directory, maximum_observations,
         movingaverage_window, process_events):

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

    # Get experiment name from filename
    exp_name = ''
    regex = re.compile('^cyclesdata-(.*).csv$')
    m = regex.match(basename(input_file))
    if (m):
        exp_name = m.group(1)
    else:
        logger.error('No match found in filename. ' +
                     'Input file does not follow convention ' +
                     '"cyclesdata-(.*).csv"')
        logger.info('Exiting program due to error.')
        exit(1)
    assert exp_name != ''

    # If events data file must be processed, also read this input file.
    # Pre condition for this to work: all cycles data files must follow
    # the regex /^cyclesdata-(.*).csv$/
    dfevents = None
    if process_events:
        filename = 'eventsdata-' + exp_name + '.csv'
        logger.debug('Events data file should be {}.'.format(filename))
        f = join('report/data', filename)
        if isfile(f):
            dfevents = pd.read_csv(f, sep=' ')
            logger.debug('Have read the events dataframe.')
        else:
            logger.warning('Could not found corresponding events ' +
                           'filename {}.'.format(f))
            process_events = False
    # assert process_events is (dfevents is not None)
    if dfevents is None:
        logger.warning('dfevents is None!')

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

    config_series_list = df.config_series.unique()
    if len(config_series_list) != 1:
        logger.warning('The uniqueness of the number of config_series ' +
                       ' is not 1!')
    config_series = remove_quotes(config_series_list[0])
    # assertion: number of cores must equal the length of the config string
    if len(config_series) != cores:
        logger.warning('Length of config_series string is not equal number of cores!')
    logger.debug('config_series={}'.format(config_series))

    config_bench_list = df.config_benchmarks.unique()
    if len(config_bench_list) != 1:
        logger.warning('The uniqueness of the number of config_bench ' +
                       ' is not 1!')
    config_bench = remove_quotes(config_bench_list[0])
    # assertion: number of cores must equal the length of the config string
    if len(config_bench) != cores:
        logger.warning('Length of config_bench string is not equal number of cores!')
    logger.debug('config_bench={}'.format(config_bench))

    pattern_list = df.pattern.unique()
    if len(pattern_list) != 1:
        logger.warning('The uniqueness of the pattern column values is not 1!')
    pattern = remove_quotes(pattern_list[0])
    logger.debug('pattern={}'.format(pattern))

    benchmarks = [benchmark_list[int(tup[0])-1][int(tup[1])-1]
                  for tup in zip(config_series, config_bench)]
    logger.debug('benchmarks={}'.format(benchmarks))

    # Start constructing output filename
    output_filename = 'cycles{}-{}-'.format('data', exp_name)
    output_filename += '{}core-'.format(cores)
    output_filename += 'configseries{}-'.format(config_series)
    output_filename += 'configbench{}-'.format(config_bench)
    output_filename += '{}{}'.format('pattern', pattern)

    if dfevents is not None:
        dfevents = dfevents.set_index(keys=['core', 'pmu'])
        dfevents['eventname'] = dfevents['eventtype'].apply(lambda x: int(x, 16))
        dfevents['eventname'] = dfevents['eventname'].apply(event_number2name)
        dfevents.sort_index(inplace=True)
        logger.debug('cores in events dataframe:' +
                     '{}'.format(set(dfevents.index.get_level_values(0))))
        logger.debug('PMUs in events dataframe:' +
                     '{}'.format(set(dfevents.index.get_level_values(1))))
        nr_of_pmus = len(set(dfevents.index.get_level_values(1)))
        for pmu in range(1, nr_of_pmus+1):
            pmu_filename = output_filename + '-PMU{}'.format(pmu) + '.png'
            outfile = join(output_directory, pmu_filename)
            output_image(df, cores, dfevents, pmu, win, benchmarks,
                         exp_label, outfile)

    else:
        output_filename += '.png'
        logger.debug('output_filename={}'.format(output_filename))
        outfile = join(output_directory, output_filename)
        output_image(df, cores, None, 0, win, benchmarks,
                     exp_label, outfile)


def output_image(dfcycles, cores, dfevents, pmu, win, benchmarks,
                 exp_label, outfile):

    fig_height = 4 + 3 * cores
    fig, ax = plt.subplots(cores, 1, sharey=True, figsize=(20, fig_height))
    left = 0.145   # the left side of the subplots of the figure
    right = 0.92   # the right side of the subplots of the figure
    bottom = 0.15  # the bottom of the subplots of the figure
    top = 0.9      # the top of the subplots of the figure
    wspace = 0.3   # the amount of width reserved for space between subplots,
                   # expressed as a fraction of the average axis width
    hspace = 0.5   # the amount of height reserved for space between subplots,
                   # expressed as a fraction of the average axis height
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top,
                        wspace=wspace, hspace=hspace)

    for corenum in range(cores):
        dfcore = dfcycles.loc[dfcycles['core'] == corenum]
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
        if cores == 1:
            axi = ax
        else:
            axi = ax[corenum]
        axi.set_ylabel('Cycles')
        axi.plot(dfcore.index, dfcore[field2plot], label=label,
                 marker='o', linestyle=None, color='blue')
        axi.legend(loc=1)
        axi.grid(True)
        if dfevents is not None:
            try:
                logger.debug('Adding PMU plot')
                logger.debug(dfevents.index)
                dfcore_ev = dfevents.loc[(corenum, pmu), slice(None)]
                dfcore_ev = dfcore_ev.set_index(keys=['iteration'])
                eventname = dfcore_ev['eventname'].unique()[0]
                ax2 = axi.twinx()
                ax2.plot(dfcore_ev.index, dfcore_ev['eventcount'],
                         marker='o', linestyle=None, color='green',
                         label=eventname)
                ax2.set_ylabel(eventname)
                ax2.legend(loc=4)
            except KeyError:
                logger.warning('Caught KeyError, core is {}, '.format(corenum) +
                               'PMU is {}'.format(pmu))

    if cores == 1:
        ax.set_title(exp_label)
        ax.set_xlabel('Iteration')
    else:
        ax[0].set_title(exp_label)
        ax[cores-1].set_xlabel('Iteration')

    plt.savefig(outfile)


if __name__ == "__main__":
    main()
