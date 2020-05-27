#ifndef xRTOS_CONFIG_H
#define xRTOS_CONFIG_H

/**
 * Extension of xRTOS with machinery to perform benchmark
 * evaluations.
 *
 * These are the benchmarks:
 * 0: mälardalen bsort 100
 * 1: mälardalen edn
 * 2: linear array access
 * 3: random array access
 */
#define NR_OF_CORES 3
#define BENCH_CONFIG_CORE0_1
#define BENCH_CONFIG_CORE1_2
#define BENCH_CONFIG_CORE2_3
#define CONFIG_STRING "configuration: '123'"

#define BENCH_STRING_CORE0 "benchmark: malardalen_bsort100"
#define BENCH_STRING_CORE1 "benchmark: malardalen_edn"
#define BENCH_STRING_CORE2 "benchmark: linear_array_access"
#define BENCH_STRING_CORE3 ""

#define BENCH_ARG_CORE0 Array1
#define BENCH_ARG_CORE2 mydata3

#define DO_BENCH_CORE0 bsort100_BubbleSort(BENCH_ARG_CORE0);
#define DO_BENCH_CORE1 edn_Calculate();
#define DO_BENCH_CORE2 array_access_linear(BENCH_ARG_CORE2);
#define DO_BENCH_CORE3

#define EXP_LABEL "DEFAULT"

/**
 * If the following macro with name BENCHMARK_CONFIG_M4 was
 * specified on the command line, then we know the include
 * file can be included.
 * This is done to make sure that the include file is actually
 * generated (which is done using m4).
 *
 * Usage is thus:
 *   m4 config='123' benchmark_config.m4 > benchmark_config.h && \
 *     make BENCHMARK_CONFIG=-DBENCHMARK_CONFIG_M4 Pi-64
 *
 * Or, just 
 *   make Pi-64 in case the benchmark config is not to be set.
 */
#ifdef BENCHMARK_CONFIG_M4
#include "benchmark_config.h"
#endif


#define MAX_CPU_CORES							( 4	)				// The Raspberry Pi3 has 4 cores	
#define MAX_TASKS_PER_CORE						( 8 )				// For the moment task storage is static so we need some size

/**
 * CT set Timer tick frequency.
 * If provided by the user in the benchmark_config.h use this define.
 * Else default to 10kHz, effectively setting interrupts at every
 * 120,000 cylces instead of 1,200,000 cycles (which was for the original
 * tickrate of 1KHz).
 */
#ifdef TICK_RATE_HZ
#define configTICK_RATE_HZ						( TICK_RATE_HZ )		// Timer tick frequency
#else
#define configTICK_RATE_HZ						( 10000 )				// Timer tick frequency
#endif

#define tskIDLE_PRIORITY						( 0	)				// Idle priority is 0 .. rarely would this ever change	
#define configMAX_TASK_NAME_LEN					( 16 )				// Maxium length of a task name
#define configMINIMAL_STACK_SIZE				( 128 )				// Minimum stack size used by idle task


#endif 

