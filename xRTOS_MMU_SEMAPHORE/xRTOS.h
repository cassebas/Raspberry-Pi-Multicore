#ifndef xRTOS_CONFIG_H
#define xRTOS_CONFIG_H

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

