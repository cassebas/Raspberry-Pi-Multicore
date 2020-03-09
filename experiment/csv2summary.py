import click
from os.path import isfile, join
import numpy as np
import pandas as pd
from itertools import product


benchmarks = ['malardalenbsort100',
              'malardalenedn',
              'lineararrayaccess',
              'randomarrayaccess']


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

    # Construct a pivot table: benchmarks/core will be indexed as columns,
    # to be able to easily select cycles from resulting CSV files within LaTeX.
    #    ('cores' == nr of cores,  'core' == core number)
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
    for cores in range(1, 5):
        # A list of strings with the cores, like ['core0', 'core1', ..]
        cidx = ['core'+str(i) for i in range(cores)]
        for prod in product(benchmarks, repeat=cores):
            # prod is a tuple with the names of the benchmarks, where each
            # tuple in the iterator is member of the cartesian product of all
            # benchmarks. Each tuple thus can represent a specific
            # configuration of benchmarks running on cores in a specified
            # order.
            if len(set(prod)) == 1:
                # All the same benchmarks, simple case
                bench = prod[0]
                bench_idx = benchmarks.index(bench) + 1
                config = '\'' + str(bench_idx) * cores + '\''

                # First construct the complete pivot table where this specific
                # benchmark, all configs and wanted cores (cidx) are listed.
                if config in pv.index.get_level_values(1):
                    pv_tmp = pv.loc[(cores, config, slice(None)),
                                    (slice(None), bench, cidx)]
                    pv_tmp.dropna(how='any', inplace=True)
                    pv_tmp.columns = pv_tmp.columns.to_series().str.join('-')
                    # write to CVS output file
                    output_file = 'cycles-{}core-{}.csv'.format(cores, bench)
                    outfile = join(output_directory, output_file)
                    pv_tmp.to_csv(outfile, index=True, sep=' ')
            else:
                # Not all the same benchmarks: we have to do some tricks to
                # make sure the pivot table contains only the rows that are
                # relevant to the exact (ordered) combination of benchmarks
                # running on specific cores.
                bench_list = list(prod)
                config = '\''
                for i in range(cores):
                    bench_idx = benchmarks.index(bench_list[i]) + 1
                    config += str(bench_idx)
                config += '\''

                # pv_cb: selection of pv with all prod's benchmarks and cores
                #        in cidx:
                if config in pv.index.get_level_values(1):
                    pv_cb = pv.loc[(cores, config, slice(None)),
                                    (slice(None), bench_list[0], cidx[0])]
                    for i in range(1, cores):
                        pv_tmp = pv.loc[(cores, config, slice(None)),
                                        (slice(None), bench_list[i], cidx[i])]
                        pv_cb = pd.merge(pv_cb, pv_tmp,
                                         left_index=True,
                                         right_index=True)
                    pv_cb.dropna(how='any', inplace=True)

                    if len(pv_cb.index) > 0:
                        # We have results for this configuration!
                        pv_cb.columns = pv_cb.columns.to_series().str.join('-')
                        bench_str = '-'.join(prod)
                        output_file = ('cycles-{}core-'.format(cores) +
                                       bench_str + '.csv')
                        outfile = join(output_directory, output_file)
                        pv_cb.to_csv(outfile, index=True, sep=' ')


if __name__ == "__main__":
    main()
