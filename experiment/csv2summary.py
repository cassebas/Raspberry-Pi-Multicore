import click
from os.path import basename, isfile, join
import numpy as np
import pandas as pd
import re


benchmarks = ['malardalenbsort100',
              'malardalenedn',
              'lineararrayaccess',
              'randomarrayaccess']


def remove_quotes(str):
    str = re.sub(r'^\'', '', str)
    str = re.sub(r'\'$', '', str)
    return str


@click.command()
@click.option('--input-file',
              help='Path and filename of the input file.')
@click.option('--output-directory',
              default='report/data',
              help='Path of the output directory.')
def main(input_file, output_directory):
    if not isfile(input_file):
        print('Error: input file {}'.format(input_file), end=' ')
        print('does not exist!')
        exit(1)

    print('Processing input file {}.'.format(input_file))
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

    # Construct a pivot table:
    #  - benchmarks/core will be indexed as columns,
    #  - cores, configuration, dassign, pattern will be the index
    # From this pivot table we can easily select the median/std cycles and
    # output them to specific CSV files for specific benchmarks/config/dassign.
    # These resulting CSV files are read from within LaTeX.
    #    (Note: 'cores' == nr of cores,  'core' == core number)
    pv = pd.pivot_table(df,
                        index=['cores', 'configuration', 'dassign', 'pattern'],
                        columns=['benchmark', 'core'],
                        values='cycles',
                        aggfunc={'cycles': [np.median, np.std]})
    pv = pv.rename(columns={0: 'core0',
                            1: 'core1',
                            2: 'core2',
                            3: 'core3'})
    pv.sort_index(inplace=True)

    # Now output a series of CVS files that contain the summaries
    # The index levels of the pv dataframe are:
    #  - level 0: number of cores
    #  - level 1: configuration string
    #  - level 2: data assignment string
    #  - level 3: alignment pattern string
    for cores in range(1, 5):
        cidx = ['core'+str(i) for i in range(cores)]
        for config in set(pv.index.get_level_values(1)):
            for dassign in set(pv.index.get_level_values(2)):
                try:
                    pv_summary = pv.loc[(cores, config, dassign, slice(None)),
                                        (slice(None), slice(None), cidx)]
                    pv_summary.dropna(axis=0, how='all', inplace=True)
                    pv_summary.dropna(axis=1, how='all', inplace=True)
                    if len(pv_summary.index) > 0:
                        pv_summary.columns = pv_summary.columns.to_series().str.join('-')
                        ca = remove_quotes(config)
                        da = remove_quotes(dassign)
                        output_filename = '{}-cycles-config{}-dassign{}-{}core.csv'.format(logname, ca, da, cores)
                        outfile = join(output_directory, output_filename)
                        pv_summary.to_csv(outfile, index=True, sep=' ')
                except KeyError:
                    print('KeyError => cores={} config={} dassign={}'.format(cores, config, dassign))
            for pattern in set(pv.index.get_level_values(3)):
                try:
                    pv_summary = pv.loc[(cores, config, slice(None), pattern),
                                        (slice(None), slice(None), cidx)]
                    pv_summary.dropna(axis=0, how='all', inplace=True)
                    pv_summary.dropna(axis=1, how='all', inplace=True)
                    if len(pv_summary.index) > 0:
                        pv_summary.columns = pv_summary.columns.to_series().str.join('-')
                        ca = remove_quotes(config)
                        pa = remove_quotes(pattern)
                        output_filename = '{}-cycles-config{}-pattern{}-{}core.csv'.format(logname, ca, pa, cores)
                        outfile = join(output_directory, output_filename)
                        pv_summary.to_csv(outfile, index=True, sep=' ')
                except KeyError:
                    print('KeyError => cores={} config={} dassign={}'.format(cores, config, dassign))


if __name__ == "__main__":
    main()
