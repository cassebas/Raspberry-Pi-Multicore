changecom(%)dnl
dnl % This is an autogenerated tex file, do NOT edit!
dnl % It is generated by the use of m4 macros.
dnl %
dnl % These are the benchmarks:
dnl % 1: mälardalen bsort 100
dnl % 2: mälardalen edn
dnl % 3: linear array access
dnl % 4: random array access
dnl %
dnl % The BENCH_CONFIG definition prescribes the specific benchmarks running
dnl % on the specific cores. If only one benchmark runs on multiple cores, the
dnl % NR_OF_CORES definition says on how many cores the benchmark is run.
dnl %
dnl % This m4 macro file expects the following 3 parameters:
dnl %  -Dfilename: filename of the CSV file containing the data
dnl %  -Dconfig: configuration of cores/benchmarks, like e.g. '3344'
dnl %  -Ddtype: type of data in the figure to plot, either 'pattern' or 'dassign'
dnl %
divert(`-1')
define(`forloop', `pushdef(`$1', `$2')_forloop($@)popdef(`$1')')
define(`_forloop',
`$4`'ifelse($1, `$3', `', `define(`$1', incr($1))$0($@)')')
dnl
define(nr_of_benchmarks, 4)dnl
define(bench_name1, malardalenbsort100)dnl
define(bench_name2, malardalenedn)dnl
define(bench_name3, lineararrayaccess)dnl
define(bench_name4, randomarrayaccess)dnl
define(bench_name, undefined)
dnl
dnl % These are the default parameters:
ifdef(`config', `', `define(config, `123')')
ifdef(`dtype', `', `define(dtype, `dassign')')
dnl %   but they can be redefined on the cmd line with:
dnl %  -Dconfig='foo' => redefine config as foo
dnl %  -Ddtype='bar'  => redefine dtype as bar
dnl % e.g.
dnl % m4 -Dconfig='1234' -Ddtype='pattern' maketex-cyclesummaries.m4
dnl
dnl % meta1 : runs a for loop from 0 to 3 where each iteration a specified macro is executed
define(meta1, `forloop(`i', `0', `3', `$1(i)')')dnl
define(meta2, `forloop(`i', `0', `3', `forloop(`j', `1', nr_of_benchmarks, `$1(i`_'j)')')')dnl
define(meta3, `forloop(`i', `0', eval(len($1) - 1), `$2($3,`bench_name_from_config'`('i`)',i)')')
dnl
define(lookup_name, `bench_name'$1)dnl
dnl
dnl % bench_name_def
dnl %   parameters:
dnl %     $1 number of the benchmark to lookup
dnl % define(bench_name_from_config, `lookup_name(substr(config, eval($1-1), `1'))')
define(bench_name_from_config, `lookup_name(substr(config, $1, `1'))')
dnl
dnl % template_addplot
dnl %   parameters:
dnl %     $1 filename of input CSV file
dnl %     $2 benchmark name
dnl %     $3 core number
define(template_addplot, `
      \addplot+[]
      plot [
        error bars/.cd,
        y dir = both,
        y explicit,
      ] dtype config
      table [
        x expr = \coordindex,
        y expr = \thisrow{median-$2-core$3},
        y error expr = \thisrow{std-$2-core$3},
      ] {data/$1};
      \addlegendentry{Core $3}')dnl
dnl
dnl % template_figure
dnl %   parameters:
dnl %     $1 filename of input CSV file
dnl %     $2 number of cores
define(template_figure, `dnl
\begin{figure}
  \centering
  \begin{tikzpicture}
    \begin{axis}
      [
        ybar,
        xlabel={Alignment pattern --- number of ticks for each cores starting time},
        ylabel={Cycles},
        flexible xticklabels from table={data/$1}{dtype}{},
        xtick=data,
        x tick label style={rotate=45, anchor=north east, inner sep=0mm},
        % ytick distance=0.25,
        % ymin=0,
        % grid=major,
        bar width=0.3,
        enlarge x limits=0.5,
        legend style={at={(0.98,0.70)},anchor=south east},
        % nodes near coords,
      ]

      meta3(`config', `template_addplot', `filename')

    \end{axis}
  \end{tikzpicture}
  \caption{Benchmarks running on $2 cores}
  \label{`fig_cycles_'config`_'$2`_cores'}
\end{figure}')dnl
divert(0)dnl
dnl
template_figure(`filename', 4)
