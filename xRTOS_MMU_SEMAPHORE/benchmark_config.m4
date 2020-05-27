changecom(/*,*/)dnl
#ifndef BENCHMARK_CONFIG_H
#define BENCHMARK_CONFIG_H
/**
 * This is an autogenerated header file, do NOT edit!
 * It is generated by the use of m4 macros.
 *
 * These are the benchmarks:
 * 1: mälardalen bsort 100
 * 2: mälardalen edn
 * 3: linear array access
 * 4: linear array write
 * 5: random array access
 * 6: random array write
 *
 * The BENCH_CONFIG definition prescribes the specific benchmarks running
 * on the specific cores. If only one benchmark runs on multiple cores, the
 * NR_OF_CORES definition says on how many cores the benchmark is run.
 */
divert(`-1')
/* Define forloop for iteration within m4 */
/* forloop(var, from, to, stmt) - simple version, taken from GNU manual */
define(`forloop', `pushdef(`$1', `$2')_forloop($@)popdef(`$1')')
define(`_forloop',
`$4`'ifelse($1, `$3', `', `define(`$1', incr($1))$0($@)')')
divert`'dnl
/* Default number of benchmarks is 6 (but can be altered on the m4-cmdline) */
define(nr_of_benchmarks, 6)dnl
/* Default configuration of benchmarks is '123' (but can be altered on the m4-cmdline) */
define(config, `123')dnl
/* Default number of PMUs is 4 (but can be altered on the m4-cmdline) */
define(nr_of_pmus, 4)dnl
/* Default event count configuration is '01' */
define(eventscore0, `01')dnl
define(bench_string_core_undef, `
#ifdef BENCH_STRING_CORE`$1'
#undef BENCH_STRING_CORE`$1'
#endif')dnl
define(bench_arg_core_undef, `
#ifdef BENCH_ARG_CORE`$1'
#undef BENCH_ARG_CORE`$1'
#endif')dnl
define(bench_config_core_undef, `
#ifdef BENCH_CONFIG_CORE`$1'
#undef BENCH_CONFIG_CORE`$1'
#endif')dnl
define(do_bench_core_undef, `
#ifdef DO_BENCH_CORE`$1'
#undef DO_BENCH_CORE`$1'
#endif')dnl
define(pmu_event_core_undef, `
#ifdef PMU_EVENT_CORE`$1'
#undef PMU_EVENT_CORE`$1'
#endif')dnl
define(meta1, `forloop(`i', `0', `3', `$1(i)')')dnl
define(meta2, `forloop(`i', `0', `3', `forloop(`j', `1', nr_of_benchmarks, `$1(i`_'j)')')')dnl
define(meta2b, `forloop(`i', `0', `3', `forloop(`j', `1', nr_of_pmus, `$1(i`_'j)')')')dnl
dnl
/**
 * Benchmark name macros for lookup function
 */
define(bench_name1, malardalen_bsort100)dnl
define(bench_name2, malardalen_edn)dnl
define(bench_name3, linear_array_access)dnl
define(bench_name4, linear_array_write)dnl
define(bench_name5, random_array_access)dnl
define(bench_name6, random_array_write)dnl
define(lookup_name, bench_name$1)dnl

define(bench_arg1, Array$1)dnl
define(bench_arg2)dnl
define(bench_arg3, mydata$1)dnl
define(bench_arg4, mydata$1)dnl
define(bench_arg5, `mydata$1, myrandidx$1')dnl
define(bench_arg6, `mydata$1, myrandidx$1')dnl
define(lookup_arg, bench_arg$1($2))dnl

define(do_bench1, bsort100_BubbleSort(BENCH_ARG_CORE`$1');)dnl
define(do_bench2, edn_Calculate();)dnl
define(do_bench3, array_access_linear(BENCH_ARG_CORE`$1');)dnl
define(do_bench4, array_write_linear(BENCH_ARG_CORE`$1');)dnl
define(do_bench5, array_access_random(BENCH_ARG_CORE`$1');)dnl
define(do_bench6, array_write_random(BENCH_ARG_CORE`$1');)dnl
define(lookup_bench, do_bench$1($2))dnl
/**
 * Macro for generation of the defines that describe the
 * configuration of the cores and specific benchmarks running
 * on them.
 *  (e.g. BENCH_CONFIG_CORE0_2 => Core 0 runs 2nd benchmark)
 */
define(bench_config_core_def, `
#define BENCH_CONFIG_CORE`$1'_`'substr(config, $1, 1)')dnl
dnl
define(bench_string_core_def, `
#define BENCH_STRING_CORE`$1' "benchmark: lookup_name(substr(config, $1, 1))"')dnl
define(bench_string_core_empty_def, `
#define BENCH_STRING_CORE`$1' ""')dnl
dnl
define(bench_arg_core_def, `
#define BENCH_ARG_CORE`$1' lookup_arg(substr(config, $1, 1), eval($1+1))')dnl
define(bench_arg_core_empty_def, `
#define BENCH_ARG_CORE`$1' $2')dnl
dnl
define(do_bench_core_def, `
#define DO_BENCH_CORE`$1' lookup_bench(substr(config, `$1', 1), `$1')')dnl
define(do_bench_core_empty_def, `
#define DO_BENCH_CORE`$1' $2')dnl
dnl
define(pmu_event0, `(PMU_L1D_CACHE_REFILL)')dnl
define(pmu_event1, `(PMU_L1D_CACHE)')dnl
define(pmu_event2, `(PMU_BR_MIS_PRED)')dnl
define(pmu_event3, `(PMU_BR_PRED)')dnl
define(pmu_event4, `(PMU_MEM_ACCESS)')dnl
define(pmu_event5, `(PMU_L1D_CACHE_WB)')dnl
define(pmu_event6, `(PMU_L2D_CACHE)')dnl
define(pmu_event7, `(PMU_L2D_CACHE_REFILL)')dnl
define(pmu_event8, `(PMU_L1D_CACHE_WB)')dnl
define(pmu_event9, `(PMU_BUS_ACCESS)')dnl
define(lookup_pmu, pmu_event$1)dnl
dnl
define(meta3, `forloop(`i', `0', eval(len($1) - 1), `$2(i)')')dnl
define(meta4, `forloop(`i', len($1), 3, `$2(i)')')dnl
divert(0)dnl
dnl
meta1(`bench_string_core_undef')dnl
meta1(`bench_arg_core_undef')dnl
meta1(`do_bench_core_undef')dnl
meta2(`bench_config_core_undef')dnl
meta2b(`pmu_event_core_undef')dnl

meta3(`config', `bench_config_core_def')dnl
dnl
meta3(`config', `bench_string_core_def')dnl
ifelse(len(config), 4, `', `meta4(`config', `bench_string_core_empty_def')')dnl
dnl
meta3(`config', `bench_arg_core_def')dnl
ifelse(len(config), 4, `', `meta4(`config', `bench_arg_core_empty_def')')dnl
dnl
meta3(`config', `do_bench_core_def')dnl
ifelse(len(config), 4, `', `meta4(`config', `do_bench_core_empty_def')')

#ifdef CONFIG_STRING
#undef CONFIG_STRING
#endif
#define CONFIG_STRING "configuration: 'config'"dnl

define(nr_of_cores, 4)
#ifdef NR_OF_CORES
#undef NR_OF_CORES
#endif
#define NR_OF_CORES len(config)
dnl

/* The PMU event count configuration */dnl
define(pmu_core_def, `
#define PMU_EVENT_CORE`$1'_`'eval($2+1)`' `'lookup_pmu(substr(pmu_core$1, $2, 1))')dnl
dnl
define(pmu_core_def0, `pmu_core_def(0, $1)')dnl
define(pmu_core_def1, `pmu_core_def(1, $1)')dnl
define(pmu_core_def2, `pmu_core_def(2, $1)')dnl
define(pmu_core_def3, `pmu_core_def(3, $1)')dnl
ifdef(`pmu_core0', meta3(`pmu_core0', `pmu_core_def0'))dnl
ifdef(`pmu_core1', meta3(`pmu_core1', `pmu_core_def1'))dnl
ifdef(`pmu_core2', meta3(`pmu_core2', `pmu_core_def2'))dnl
ifdef(`pmu_core3', meta3(`pmu_core3', `pmu_core_def3'))dnl

dnl maybe use a label that is used by the data visualization scripts
ifdef(`exp_label', `', `define(exp_label, `default')')
#ifdef EXP_LABEL
#undef EXP_LABEL
#define EXP_LABEL "exp_label"
#endif

dnl maybe define the tick rate in Hz
define(tick_rate_hz_template, `
#ifdef TICK_RATE_HZ
#undef TICK_RATE_HZ
#endif
#define TICK_RATE_HZ $1
')dnl
ifdef(`tick_rate_hz', `tick_rate_hz_template(tick_rate_hz)', `')

#endif /* ~BENCHMARK_CONFIG_H */
