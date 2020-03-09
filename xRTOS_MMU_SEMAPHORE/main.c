#include <stdint.h>
#include <string.h>
#include "rpi-smartstart.h"
#include "emb-stdio.h"
#include "xRTOS.h"
#include "task.h"
#include "windows.h"
#include "semaphore.h"

/* definition of performance monitor control registers and such */
#include "armv8_pm.h"
/* our own synthetic benchmark for testing purposes */
#include "synthetic_bench.h"
#include "malardalen.h"

/* cache invalidation */
#include "iv_cache.h"

/**
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
#define BENCH_STRING_CORE3 "benchmark: random_array_access"

#define BENCH_ARG_CORE0 Array1
#define BENCH_ARG_CORE2 mydata3

#define DO_BENCH_CORE0 bsort100_BubbleSort(BENCH_ARG_CORE0);
#define DO_BENCH_CORE1 edn_Calculate();
#define DO_BENCH_CORE2 array_access_linear(BENCH_ARG_CORE2);
#define DO_BENCH_CORE3

/* The random data sets can be assigned to different cores,
   to make sure that the data cannot be a factor in the measured
   cycles. */
#define DATA_ASSIGN_CORE0 0
#define DATA_ASSIGN_CORE1 1
#define DATA_ASSIGN_CORE2 2
#define DATA_ASSIGN_CORE3 3
#define DATA_ASSIGN_STRING "dassign: '0123'"

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

/**
 * Maybe define the needed datastructures (depending on
 * the specific configuration of benchmarks).
 */
#ifdef BENCH_CONFIG_CORE0_1
int Array1[MAXDIM];
#endif
#ifdef BENCH_CONFIG_CORE1_1
int Array2[MAXDIM];
#endif
#ifdef BENCH_CONFIG_CORE2_1
int Array3[MAXDIM];
#endif
#ifdef BENCH_CONFIG_CORE3_1
int Array4[MAXDIM];
#endif

#ifdef BENCH_CONFIG_CORE0_3
volatile bigstruct_t mydata1[SYNBENCH_DATASIZE];
#else
	#ifdef BENCH_CONFIG_CORE0_4
	volatile bigstruct_t mydata1[SYNBENCH_DATASIZE];
	volatile int myrandidx1[SYNBENCH_DATASIZE];
	#endif
#endif
#ifdef BENCH_CONFIG_CORE1_3
volatile bigstruct_t mydata2[SYNBENCH_DATASIZE];
#else
	#ifdef BENCH_CONFIG_CORE1_4
	volatile bigstruct_t mydata2[SYNBENCH_DATASIZE];
	volatile int myrandidx2[SYNBENCH_DATASIZE];
	#endif
#endif
#ifdef BENCH_CONFIG_CORE2_3
volatile bigstruct_t mydata3[SYNBENCH_DATASIZE];
#else
	#ifdef BENCH_CONFIG_CORE2_4
	volatile bigstruct_t mydata3[SYNBENCH_DATASIZE];
	volatile int myrandidx3[SYNBENCH_DATASIZE];
	#endif
#endif
#ifdef BENCH_CONFIG_CORE3_3
volatile bigstruct_t mydata4[SYNBENCH_DATASIZE];
#else
	#ifdef BENCH_CONFIG_CORE3_4
	volatile bigstruct_t mydata4[SYNBENCH_DATASIZE];
	volatile int myrandidx4[SYNBENCH_DATASIZE];
	#endif
#endif


static inline uint64_t armv8pmu_pmcr_read(void)
{
    uint64_t val = 0;
    asm volatile ("mrs %0, pmcr_el0" : "=r" (val));
    return val;
}

static inline uint64_t armv8pmu_pmccntr_read(void)
{
    uint64_t val = 0;
	asm volatile("mrs %0, pmccntr_el0" : "=r" (val));
    return val;
}

static inline uint64_t armv8pmu_pmcntenset_read(void)
{
    uint64_t val = 0;
    asm volatile("mrs %0, pmcntenset_el0" : "=r" (val));
    return val;
}

static inline void armv8pmu_pmcr_write(uint64_t val)
{
    val &= ARMV8_PMCR_MASK;
	asm volatile("isb");
	asm volatile("msr pmcr_el0, %0" : : "r" (val));
}

static inline uint64_t read_counter()
{
	/* Access cycle counter */
	uint64_t val = 0;
	asm volatile("mrs %0, pmccntr_el0" : "=r" (val));
	return val;
}

static inline void enable_counters()
{
	/*Enable user-mode access to counters. */
	uint64_t pmuserenr = ((uint64_t) ARMV8_PMUSERENR_EN_EL0|ARMV8_PMUSERENR_ER|ARMV8_PMUSERENR_CR);
	asm volatile("msr pmuserenr_el0, %0" : : "r" (pmuserenr));
    asm volatile("msr pmccfiltr_el0, %0" : : "r" (ARMV8_PMCCFILTR_EL0));
    // asm volatile("msr pmccfiltr_el0, %0" : : "r" (0));

	/* Performance Monitors Count Enable Set register bit 30:0 disable, 31 enable. */
	/* Can also enable other event counters here. */
	asm volatile("msr pmcntenset_el0, %0" : : "r" (ARMV8_PMCNTENSET_EL0_ENABLE));

	/* Enable counters */
	uint64_t val=0;
	asm volatile("mrs %0, pmcr_el0" : "=r" (val));
	asm volatile("msr pmcr_el0, %0" : : "r" (val|ARMV8_PMCR_E));
}

static void disable_counters()
{
    asm volatile("msr pmuserenr_el0, %0" : : "r" (0));
    armv8pmu_pmcr_write(armv8pmu_pmcr_read() & (~ARMV8_PMCR_E));
}



static bool lit = false;
void Flash_LED(void)
{
	if (lit) lit = false; else lit = true;							// Flip lit flag
	set_Activity_LED(lit);											// Turn LED on/off as per new flag
}



void DoProgress(HDC dc, int step, int total, int x, int y, int barWth, int barHt,  COLORREF col)
{

	// minus label len
	int pos = (step * barWth) / total;

	// Draw the colour bar
	COLORREF orgBrush = SetDCBrushColor(dc, col);
	Rectangle(dc, x, y, x+pos, y+barHt);

	// Draw the no bar section 
	SetDCBrushColor(dc, 0);
	Rectangle(dc, x+pos, y, x+barWth, y+barHt);

	SetDCBrushColor(dc, orgBrush);

}

/**
 * Invalidate data and instruction caches, all levels.
 */
void volatile invalidate_cache()
{
	__asm_invalidate_dcache_all();
	__asm_invalidate_icache_all();
}

/**
 * Invalidate data and instruction caches, single level.
 *   level = 1 => L1 cache
 *   level = 2 => L2 cache
 */
void volatile invalidate_data_cache(int level)
{
	// second parameter of __asm_dcache_level is:
	//  0 clean & invalidate, 1 invalidate only
	__asm_dcache_level(level-1, 1);
}

/**
 * Disable data entirely.
 */
void volatile disable_cache()
{
	__asm_cache_disable();
}


void core0(void* pParam) {
	char buf[256];
	HDC Dc = CreateExternalDC(5);
	COLORREF col = 0xFF00FFFF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=0;
	enable_counters();

	while (1) {
#ifdef BENCH_CONFIG_CORE0_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array1);
#endif
#ifdef BENCH_CONFIG_CORE0_4
		array_access_randomize(myrandidx1, DATA_ASSIGN_CORE0, iter);
#endif
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 100, GetScreenWidth()-20, 20, col);

#ifndef DISABLE_CACHE
	#ifndef NO_CACHE_MGMT
		/* Master gets to invalidate the complete cache */
		invalidate_cache();
	#endif
#endif

		/* This is core0, we are master for the synchronization between cores */
		sync_master();

		cycles_begin = read_counter();
		DO_BENCH_CORE0
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		sync_reset();

		xTaskDelay(50);

		sprintf(&buf[0],
				"Core 0 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 80, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "%s %s %s cores: %d Core 0 Cycle count: %12u iteration: %u offset: %d\n\r",
				 CONFIG_STRING, BENCH_STRING_CORE0, DATA_ASSIGN_STRING, NR_OF_CORES,
				 time, iter++, offset);
	}
}

void core1(void* pParam) {
	char buf[256];
	HDC Dc = CreateExternalDC(6);
	COLORREF col = 0xFFFFFFFF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=1;
	enable_counters();

	while (1) {
#ifdef BENCH_CONFIG_CORE1_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array2);
#endif
#ifdef BENCH_CONFIG_CORE1_4
		array_access_randomize(myrandidx2, DATA_ASSIGN_CORE1, iter);
#endif
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 200, GetScreenWidth() - 20, 20, col);

#ifndef DISABLE_CACHE
	#ifndef NO_CACHE_MGMT
		/* Slave only invalidates its own L1 cache */
		invalidate_data_cache(1);
	#endif
#endif

		/* This is core1, we are slave for the synchronization between cores */
		sync_slave(offset);

		cycles_begin = read_counter();
		DO_BENCH_CORE1
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		sync_reset();

		xTaskDelay(50);

		sprintf(&buf[0],
				"Core 1 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 180, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "%s %s %s cores: %d Core 1 Cycle count: %12u iteration: %u offset: %d\n\r",
				 CONFIG_STRING, BENCH_STRING_CORE1, DATA_ASSIGN_STRING, NR_OF_CORES,
				 time, iter++, offset);

		if (iter % 2000 == 0)
			offset++;
	}
}

void core2(void* pParam) {
	char buf[256];
	HDC Dc = CreateExternalDC(7);
	COLORREF col = 0xFF7F7F7F;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=2;
	enable_counters();

	while (1) {
#ifdef BENCH_CONFIG_CORE2_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array3);
#endif
#ifdef BENCH_CONFIG_CORE2_4
		array_access_randomize(myrandidx3, DATA_ASSIGN_CORE2, iter);
#endif
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 300, GetScreenWidth() - 20, 20, col);

#ifndef DISABLE_CACHE
	#ifndef NO_CACHE_MGMT
		/* Slave only invalidates its own L1 cache */
		invalidate_data_cache(1);
	#endif
#endif

		/* This is core2, we are slave for the synchroniztion between cores */
		sync_slave(offset);

		cycles_begin = read_counter();
		DO_BENCH_CORE2
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		sync_reset();

		xTaskDelay(50);

		sprintf(&buf[0],
				"Core 2 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 280, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "%s %s %s cores: %d Core 2 Cycle count: %12u iteration: %u offset: %d\n\r",
				 CONFIG_STRING, BENCH_STRING_CORE2, DATA_ASSIGN_STRING, NR_OF_CORES,
				 time, iter++, offset);

		if (iter % 2000 == 0)
			offset++;
	}
}

void core3(void* pParam) {
	char buf[256];
	HDC Dc = CreateExternalDC(8);
	COLORREF col = 0xFFFF00FF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=3;
	enable_counters();

	while (1) {
#ifdef BENCH_CONFIG_CORE3_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array4);
#endif
#ifdef BENCH_CONFIG_CORE3_4
		array_access_randomize(myrandidx4, DATA_ASSIGN_CORE3, iter);
#endif
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;

		}
		DoProgress(Dc, step, total, 10, 400, GetScreenWidth() - 20, 20, col);

#ifndef DISABLE_CACHE
	#ifndef NO_CACHE_MGMT
		/* Slave only invalidates its own L1 cache */
		invalidate_data_cache(1);
	#endif
#endif

		/* This is core3, we are slave for the synchroniztion between cores */
		sync_slave(offset);

		cycles_begin = read_counter();
		DO_BENCH_CORE3
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		sync_reset();

		xTaskDelay(50);

		sprintf(&buf[0],
				"Core 3 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 380, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "%s %s %s cores: %d Core 3 Cycle count: %12u iteration: %u offset: %d\n\r",
				 CONFIG_STRING, BENCH_STRING_CORE3, DATA_ASSIGN_STRING, NR_OF_CORES,
				 time, iter++, offset);

		if (iter % 2000 == 0)
			offset++;
	}
}

void main (void)
{
	char buf[256];

	Init_EmbStdio(WriteText);										// Initialize embedded stdio
	PiConsole_Init(0, 0, 0, printf);								// Auto resolution console, message to screen
	displaySmartStart(printf);										// Display smart start details
	ARM_setmaxspeed(printf);										// ARM CPU to max speed

	// get timer frequency
	RegType_t timerfreq = EL0_Timer_Frequency();

	printf("Task tick rate: %u   EL0 Timer frequency %u\n", configTICK_RATE_HZ, timerfreq);

    unsigned int baudrate = 115200;
    if (pl011_uart_init(baudrate)) {
        printf("UART succesfully initialized\n");
    } else {
        printf("UART could not be initialized!\n");
    }

	xRTOS_Init();													// Initialize the xRTOS system .. done before any other xRTOS call



#ifdef DISABLE_CACHE
	// Maybe disable cache completely:
	disable_cache();
	log_info(0, buf, "%s\n\r", "Cache is disabled.");
#endif


	/* Core 0 task */
	xTaskCreate(0, core0, "Core0", 512, NULL, 2, NULL);

#if(NR_OF_CORES >= 2)
	/* Core 1 task */
	xTaskCreate(1, core1, "Core1", 512, NULL, 2, NULL);
#endif

#if(NR_OF_CORES >= 3)
	/* Core 2 task */
	xTaskCreate(2, core2, "Core2", 512, NULL, 2, NULL);
#endif

#if(NR_OF_CORES >= 4)
	/* Core 3 task */
	xTaskCreate(3, core3, "Core3", 512, NULL, 2, NULL);
#endif


	/* Start scheduler */
	xTaskStartScheduler();

	/*
	 *	We should never get here, but just in case something goes wrong,
	 *	we'll place the CPU into a safe loop.
	 */
	while (1) {
		log_warning(0, buf, "%s\n\r", "Main program reached safe loop, this should not happen!");
	}
}
