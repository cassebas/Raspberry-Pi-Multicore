import click
from os.path import isdir, join
import numpy as np
import pandas as pd
import glob
from itertools import product


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

            # Construct a pivot table: benchmarks/core will be indexed as columns,
            # to be able to easily select cycles from resulting CSV files within LaTeX.
            #    ('cores' == nr of cores,  'core' == core number)
            pv = pd.pivot_table(df,
                                index=['cores', 'configuration', 'pattern'],
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
        for cores in range(1, 5):
            # A list of strings with the cores, like ['core0', 'core1', ..]
            cidx = ['core'+str(i) for i in range(cores)]
            for prod in product(benchmarks, repeat=cores):
                # prod is a tuple with the names of the benchmarks, where each tuple in the
                # iterator is member of the cartesian product of all benchmarks.
                # Each tuple thus can represent a specific configuration of benchmarks running
                # on cores in a specified order.
                if len(set(prod)) == 1:
                    # All the same benchmarks, simple case
                    bench = prod[0]
                    bench_idx = benchmarks.index(bench)
                    pattern = '\'' + str(bench_idx) * cores + '\''

                    # First construct the complete pivot table where this specific benchmark,
                    # all patterns and wanted cores (cidx) are listed.
                    if pattern in pvs.index.get_level_values(1):
                        pvs_tmp = pvs.loc[(cores, pattern, slice(None)),
                                          (slice(None), bench, cidx)]
                        pvs_tmp.dropna(how='any', inplace=True)
                        pvs_tmp.columns = pvs_tmp.columns.to_series().str.join('-')
                        # write to CVS output file
                        output_file = 'cycles-{}core-{}.csv'.format(cores, bench)
                        outfile = join(output_directory, output_file)
                        pvs_tmp.to_csv(outfile, index=True, sep=' ')
                else:
                    # Not all the same benchmarks: we have to do some tricks to make sure
                    # the pivot table contains only the rows that are relevant to the exact
                    # (ordered) combination of benchmarks running on specific cores.
                    bench_list = list(prod)
                    print('\n\n\n{}'.format(bench_list))
                    pattern = '\''
                    for i in range(cores):
                        bench_idx = benchmarks.index(bench_list[i])
                        pattern += str(bench_idx)
                    pattern += '\''

                    # pvs_cb: selection of pvs with all prod's benchmarks and cores in cidx:
                    if pattern in pvs.index.get_level_values(1):
                        pvs_cb = pvs.loc[(cores, pattern, slice(None)),
                                         (slice(None), bench_list[0], cidx[0])]
                        for i in range(1, cores):
                            pvs_tmp = pvs.loc[(cores, pattern, slice(None)),
                                              (slice(None), bench_list[i], cidx[i])]
                            pvs_cb = pd.merge(pvs_cb, pvs_tmp,
                                              left_index=True,
                                              right_index=True)
                        pvs_cb.dropna(how='any', inplace=True)

                        if len(pvs_cb.index) > 0:
                            # We have results for this configuration!
                            pvs_cb.columns = pvs_cb.columns.to_series().str.join('-')
                            bench_str = '-'.join(prod)
                            output_file = ('cycles-{}core-'.format(cores) +
                                           bench_str + '.csv')
                            outfile = join(output_directory, output_file)
                            pvs_cb.to_csv(outfile, index=True, sep=' ')
                    else:
                        print('This combination of benchmarks was not run:',
                              ' '.join(prod))

    else:
        print('Warning: directory {}'.format(input_directory), end=' ')
        print('does not have any log files!')


if __name__ == "__main__":
    main()
