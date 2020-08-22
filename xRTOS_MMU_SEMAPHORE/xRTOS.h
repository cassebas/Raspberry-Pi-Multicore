#ifndef xRTOS_CONFIG_H
#define xRTOS_CONFIG_H

/**
 * Extension of xRTOS with machinery to perform benchmark
 * evaluations.
 *
 * Default configuration is 3 cores, running:
 *   Core 0: SD-VBS disparity
 *   Core 1: Mälardalen bsort
 *   Core 2: Synthetic benchmark linear array write
 */
#define NR_OF_CORES 3
#define BENCH_CONFIG_CORE0_3_1
#define BENCH_CONFIG_CORE1_2_1
#define BENCH_CONFIG_CORE2_1_2

#define CONFIG_SERIES_STRING "config_series: '321'"
#define CONFIG_BENCH_STRING "config_benchmarks: '112'"

#define BENCH_STRING_CORE0 "benchmark: sdvbs_disparity"
#define BENCH_STRING_CORE1 "benchmark: malardalen_bsort"
#define BENCH_STRING_CORE2 "benchmark: linear_array_write"
#define BENCH_STRING_CORE3 ""

#define BENCH_DECL_CORE0
#define BENCH_DECL_CORE1 volatile int* Array1;
#define BENCH_DECL_CORE2 volatile bigstruct_t* mydata2;
#define BENCH_DECL_CORE3

#define BENCH_INIT1_CORE0 \
	int width=DISPARITY_INPUTSIZE, height=DISPARITY_INPUTSIZE;	\
    int WIN_SZ=4, SHIFT=8;										\
    I2D* srcImage1 = iMallocHandle(width, height);				\
    I2D* srcImage2 = iMallocHandle(width, height);
#define BENCH_INIT1_CORE1 Array1 = (volatile int*) new int[NUMELEMS];
#define BENCH_INIT1_CORE2 mydata2 = new bigstruct_t[SYNBENCH_DATASIZE];
#define BENCH_INIT1_CORE3

#define BENCH_INIT2_CORE0 \
	for (int i=0; i<(width*height); i++) { \
		srcImage1->data[i] = rand.GetNumber() % 256; \
		srcImage2->data[i] = rand.GetNumber() % 256; \
	}
#define BENCH_INIT2_CORE1 bsort100_Initialize(Array1, &rand);
#define BENCH_INIT2_CORE2
#define BENCH_INIT2_CORE3

#define DO_BENCH_CORE0 getDisparity(srcImage1, srcImage2, WIN_SZ, SHIFT);
#define DO_BENCH_CORE1 bsort100_BubbleSort(Array1);
#define DO_BENCH_CORE2 array_write_linear(mydata2);
#define DO_BENCH_CORE3

#define BENCH_CLEANUP_CORE0
#define BENCH_CLEANUP_CORE1 free((void*) Array1);
#define BENCH_CLEANUP_CORE2 free((void*) mydata2);
#define BENCH_CLEANUP_CORE3

#define EXP_LABEL "DEFAULT"

/**
 * Specific configuration for the Mälardalen bsort benchmark
 */
#define BSORT_INPUTSIZE 100

/**
 * Specific configuration for the Mälardalen matmult benchmark
 */
#define MATMULT_INPUTSIZE 100

/**
 * Specific configuration for the Mälardalen ns benchmark
 */
#define NS_INPUTSIZE 5

/**
 * Specific configuration for the Mälardalen fir benchmark
 */
#define FIR_INPUTSIZE 700

/**
 * Specific configuration for the SD-VBS Disparity benchmark
 */
#define DISPARITY_INPUTSIZE 96

/**
 * Specific configuration for the SD-VBS mser benchmark
 */
#define MSER_INPUTSIZE 64

/**
 * Specific configuration for the SD-VBS svm benchmark
 */
#define SVM_INPUTSIZE 16

/**
 * Specific configuration for the SD-VBS stitch benchmark
 */
#define STITCH_INPUTSIZE 64

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


#define MAX_CPU_CORES							( 4 )				// The Raspberry Pi3 has 4 cores	
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

#ifndef OFFSET_INTERVAL
#define OFFSET_INTERVAL						( 100 )				// Number of iterations to run with each offset setting
#endif

#ifndef TICKS_INCR_OFFSET
#define TICKS_INCR_OFFSET						( 2 )					// Number of ticks with which the offset is increased
#endif

#define tskIDLE_PRIORITY						( 0	)				// Idle priority is 0 .. rarely would this ever change
#define configMAX_TASK_NAME_LEN				( 16 )					// Maxium length of a task name
#define configMINIMAL_STACK_SIZE				( 128 )				// Minimum stack size used by idle task


#endif 

