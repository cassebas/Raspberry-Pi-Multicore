import click
from os.path import isdir, join
import numpy as np
import pandas as pd
import glob


benchmarks = ['malardalenbsort100',
              'lineararrayaccess']


@click.command()
@click.option('--input-directory',
              default='output',
              help='Path of the input directory.')
@click.option('--output-directory',
              default='report/data',
              help='Path of the output directory.')
def main(input_directory, output_directory):
    if not isdir(input_directory):
        print('Error: input directory {}'.format(input_directory), end=' ')
        print('does not exist!')
        exit(1)

    infiles = glob.glob(join(input_directory, '*.csv'))

    if len(infiles) > 0:
        pvs = pd.DataFrame()
        for f in infiles:
            print('Processing input file {}.'.format(f))
            df = pd.read_csv(f)

            pv = pd.pivot_table(df,
                                index=['cores', 'pattern'],
                                columns=['benchmark', 'core'],
                                values='cycles',
                                aggfunc={'cycles': [np.median, np.std]})
            pvs = pd.concat([pvs, pv])
        pvs = pvs.rename(columns={0: 'core0',
                                  1: 'core1',
                                  2: 'core2',
                                  3: 'core3'})
        pvs.sort_index(inplace=True)

        # Now output a series of CVS files that contain the summaries
        for bench in benchmarks:
            for cores in range(1, 5):
                cidx = ['core'+str(i) for i in range(cores)]
                pvs_tmp = pvs.loc[cores, (slice(None), bench, cidx)]
                pvs_tmp.dropna(how='any', inplace=True)
                pvs_tmp.columns = pvs_tmp.columns.to_series().str.join('-')
                # write to CVS output file
                output_file = 'cycles-{}core-{}.csv'.format(cores, bench)
                outfile = join(output_directory, output_file)
                pvs_tmp.to_csv(outfile, index=True, sep=' ')

        # For now combinations of benchmarks hard coded:
        b1 = benchmarks[0]
        b2 = benchmarks[1]
        pvs2_0 = pvs.loc[2, (slice(None), [b1, b2], ['core0', 'core1'])]
        pvs2_0.dropna(how='all', inplace=True)

        pvs2_1 = pvs2_0.loc[:, (slice(None), b1, ['core0', 'core1'])].dropna(how='all')
        # Remove rows that are complete, these aren't combinations of
        # benchmarks but consist of the same benchmark on each core:
        pvs2_1 = pvs2_1[pvs2_1.isnull().any(1)]
        # Get the correct slice, 1st benchmark runs on core0
        pvs2_1 = pvs2_1.loc[:, (slice(None), b1, 'core0')]

        pvs2_2 = pvs2_0.loc[:, (slice(None), b2, ['core0', 'core1'])].dropna(how='all')
        # Remove rows that are complete, these aren't combinations of
        # benchmarks but consist of the same benchmark on each core:
        pvs2_2 = pvs2_2[pvs2_2.isnull().any(1)]
        # Get the correct slice, 2nd benchmark runs on core1
        pvs2_2 = pvs2_2.loc[:, (slice(None), b2, 'core1')]

        pvs_merge = pd.merge(pvs2_1, pvs2_2, left_index=True, right_index=True)
        pvs_merge.columns = pvs_merge.columns.to_series().str.join('-')

        output_file = 'cycles-{}core-{}-{}.csv'.format(2,
                                                       benchmarks[0],
                                                       benchmarks[1])
        outfile = join(output_directory, output_file)
        pvs_merge.to_csv(outfile, index=True, sep=' ')

    else:
        print('Warning: directory {}'.format(input_directory), end=' ')
        print('does not have any log files!')


if __name__ == "__main__":
    main()
