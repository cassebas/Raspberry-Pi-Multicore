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
#define BENCH_STRING_CORE3 ""

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

#define EXP_LABEL "DEFAULT"

#define PM_EVENT_TYPE1 "L2_DCACHE_ACCESS"
#define PM_EVENT_TYPE2 "L2_DCACHE_REFILL"

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

#if defined BENCH_CONFIG_CORE0_3 || defined BENCH_CONFIG_CORE0_4
volatile bigstruct_t mydata1[SYNBENCH_DATASIZE];
#else
	#if defined BENCH_CONFIG_CORE0_5 || defined BENCH_CONFIG_CORE0_6
	volatile bigstruct_t mydata1[SYNBENCH_DATASIZE];
	volatile int myrandidx1[SYNBENCH_DATASIZE];
	#endif
#endif
#if defined BENCH_CONFIG_CORE1_3 || defined BENCH_CONFIG_CORE1_4
volatile bigstruct_t mydata2[SYNBENCH_DATASIZE];
#else
	#if defined BENCH_CONFIG_CORE1_5 || defined BENCH_CONFIG_CORE1_6
	volatile bigstruct_t mydata2[SYNBENCH_DATASIZE];
	volatile int myrandidx2[SYNBENCH_DATASIZE];
	#endif
#endif
#if defined BENCH_CONFIG_CORE2_3 || defined BENCH_CONFIG_CORE2_4
volatile bigstruct_t mydata3[SYNBENCH_DATASIZE];
#else
	#if defined BENCH_CONFIG_CORE2_5 || defined BENCH_CONFIG_CORE2_6
	volatile bigstruct_t mydata3[SYNBENCH_DATASIZE];
	volatile int myrandidx3[SYNBENCH_DATASIZE];
	#endif
#endif
#if defined BENCH_CONFIG_CORE3_3 || defined BENCH_CONFIG_CORE3_4
volatile bigstruct_t mydata4[SYNBENCH_DATASIZE];
#else
	#if defined BENCH_CONFIG_CORE3_5 || defined BENCH_CONFIG_CORE3_6
	volatile bigstruct_t mydata4[SYNBENCH_DATASIZE];
	volatile int myrandidx4[SYNBENCH_DATASIZE];
	#endif
#endif

/**
 * Global enable of PMU
 */
static inline void enable_pmu()
{
	uint64_t val=0;
	asm volatile("mrs %[val], pmcr_el0" : [val]"=r" (val));
	asm volatile("msr pmcr_el0, %[val]" : : [val]"r" (val|ARMV8_PMCR_E));
}

static inline void enable_cycle_counter()
{
	asm volatile("msr pmcntenset_el0, %0" : : "r" (ARMV8_PMCNTENSET_C));
}

static void disable_cycle_counter()
{
	asm volatile("msr pmcntenclr_el0, %0" : : "r" (ARMV8_PMCNTENCLR_C));
}

static inline uint64_t read_cycle_counter()
{
	uint64_t val = 0;
	asm volatile("mrs %0, pmccntr_el0" : "=r" (val));
	return val;
}

/**
 * Reset the cycle counter PMCCNTR_EL0 to zero.
 */
static inline void reset_cycle_counter()
{
	uint64_t val=0;
	asm volatile("mrs %[val], pmcr_el0" : [val]"=r" (val));
	asm volatile("msr pmcr_el0, %[val]" : : [val]"r" (val|ARMV8_PMCR_C));
}


static inline uint64_t read_nr_eventcounters()
{
	/* Read the number of event counters, bits [15:11] in PMCR_EL0 */
	uint64_t val = 0;
	asm volatile("mrs %0, pmcr_el0" : "=r" (val));
	return ((val >> ARMV8_PMCR_N_SHIFT) & 0x1F);
}

static inline uint64_t read_cei_reg()
{
	/* Read the common event identification register */
	uint64_t val = 0;
	asm volatile("mrs %0, pmceid0_el0" : "=r" (val));
	return val;
}

static inline void config_event_counter(unsigned int counter, unsigned int event)
{
	// select the performance counter, bits [4:0] of PMSELR_EL0
	uint64_t cntr = ((uint64_t) counter & 0x1F);
	asm volatile("msr pmselr_el0, %[val]" : : [val]"r" (cntr));
	// synchronize context
	asm volatile("isb");
	// write the event type to the PMXEVTYPER
	asm volatile("msr pmxevtyper_el0, %[val]" : : [val]"r" (event & 0xFFFFFFFF));
}

static inline void enable_event_counter(unsigned int counter)
{
	uint64_t counter_bit=0;
	asm volatile(
		"mov x1, #0x1\n\t"
		"lsl %[res], x1, %[val]"
		: [res]"=r" (counter_bit)
		: [val]"r" (counter));
	asm volatile("msr pmcntenset_el0, %[val]" : : [val]"r" (counter_bit));
}

static inline void disable_event_counter(unsigned int counter)
{
	uint64_t counter_bit=0;
	asm volatile(
		"mov x1, #0x1\n\t"
		"lsl %[res], x1, %[val]"
		: [res]"=r" (counter_bit)
		: [val]"r" (counter));
	asm volatile("msr pmcntenclr_el0, %[val]" : : [val]"r" (counter_bit));
}

static inline unsigned int read_event_counter(unsigned int counter)
{
	// select the performance counter, bits [4:0] of PMSELR_EL0
	uint64_t cntr = ((uint64_t) counter & 0x1F);
	asm volatile("msr pmselr_el0, %[val]" : : [val]"r" (cntr));
	// synchronize context
	asm volatile("isb");
	// read the counter
	unsigned int events = 0;
	asm volatile("mrs %[res], pmxevcntr_el0" : [res]"=r" (events));
	return events;
}

/**
 * Reset all event counters to zero (not including PMCCNTR_EL0).
 */
static inline void reset_event_counters()
{
	uint64_t val=0;
	asm volatile("mrs %[val], pmcr_el0" : [val]"=r" (val));
	asm volatile("msr pmcr_el0, %[val]" : : [val]"r" (val|ARMV8_PMCR_P));
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
    unsigned int cycles;
#ifdef PMU_EVENT_CORE0_1
    unsigned int event1;
#endif
#ifdef PMU_EVENT_CORE0_2
    unsigned int event2;
#endif
#ifdef PMU_EVENT_CORE0_3
    unsigned int event3;
#endif
#ifdef PMU_EVENT_CORE0_4
    unsigned int event4;
#endif
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=0;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");
#ifdef PMU_EVENT_CORE0_1
	config_event_counter(0, PMU_EVENT_CORE0_1);
#endif
#ifdef PMU_EVENT_CORE0_2
	config_event_counter(1, PMU_EVENT_CORE0_2);
#endif
#ifdef PMU_EVENT_CORE0_3
	config_event_counter(2, PMU_EVENT_CORE0_3);
#endif
#ifdef PMU_EVENT_CORE0_4
	config_event_counter(3, PMU_EVENT_CORE0_4);
#endif

	while (1) {
#ifdef BENCH_CONFIG_CORE0_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array1);
#endif
#if defined BENCH_CONFIG_CORE0_5 || defined BENCH_CONFIG_CORE0_6
		array_access_randomize(myrandidx1, DATA_ASSIGN_CORE0);
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

		enable_cycle_counter();
#ifdef PMU_EVENT_CORE0_1
		enable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE0_2
		enable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE0_3
		enable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE0_4
		enable_event_counter(3);
#endif

		/* This is core0, we are master for the synchronization between cores */
		sync_master();

		/* Maybe reset the event counters */
#if defined PMU_EVENT_CORE0_1
		/* If any of the event counters is active, then at least the first one
		 * will be active. We can reset the event counters in this case. */
		reset_event_counters();
#endif
		reset_cycle_counter();
		DO_BENCH_CORE0
		disable_cycle_counter();
#ifdef PMU_EVENT_CORE0_1
		disable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE0_2
		disable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE0_3
		disable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE0_4
		disable_event_counter(3);
#endif

		sync_reset();

		xTaskDelay(10);

		cycles = read_cycle_counter();
#ifdef PMU_EVENT_CORE0_1
		event1 = read_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE0_2
		event2 = read_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE0_3
		event3 = read_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE0_4
		event4 = read_event_counter(3);
#endif

		sprintf(&buf[0],
				"Core 0 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				cycles);
		TextOut(Dc, 20, 80, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "CYCLECOUNT label: %s %s %s cores: %d core: 0 cycle_count: %12u iteration: %u offset: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, BENCH_STRING_CORE0, NR_OF_CORES,
				 cycles, iter, offset);

#ifdef PMU_EVENT_CORE0_1
		/**
		 * The first log_info statement here doesn't actually serve
		 * a purpose, other than preventing the printed event1 being
		 * zero(!). Beats me. */
		log_info(corenum, buf, "%#02x\n\r", 0x03);
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 1 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE0_1, event1, iter);
#endif
#ifdef PMU_EVENT_CORE0_2
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 2 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE0_2, event2, iter);
#endif
#ifdef PMU_EVENT_CORE0_3
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 3 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE0_3, event3, iter);
#endif
#ifdef PMU_EVENT_CORE0_4
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 4 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE0_4, event4, iter);
#endif

		++iter;
	}
}

void core1(void* pParam) {
	char buf[256];
	HDC Dc = CreateExternalDC(6);
	COLORREF col = 0xFFFFFFFF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles;
#ifdef PMU_EVENT_CORE1_1
    unsigned int event1;
#endif
#ifdef PMU_EVENT_CORE1_2
    unsigned int event2;
#endif
#ifdef PMU_EVENT_CORE1_3
    unsigned int event3;
#endif
#ifdef PMU_EVENT_CORE1_4
    unsigned int event4;
#endif
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=1;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");
#ifdef PMU_EVENT_CORE1_1
	config_event_counter(0, PMU_EVENT_CORE1_1);
#endif
#ifdef PMU_EVENT_CORE1_2
	config_event_counter(1, PMU_EVENT_CORE1_2);
#endif
#ifdef PMU_EVENT_CORE1_3
	config_event_counter(2, PMU_EVENT_CORE1_3);
#endif
#ifdef PMU_EVENT_CORE1_4
	config_event_counter(3, PMU_EVENT_CORE1_4);
#endif

	while (1) {
#ifdef BENCH_CONFIG_CORE1_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array2);
#endif
#if defined BENCH_CONFIG_CORE1_5 || defined BENCH_CONFIG_CORE1_6
		array_access_randomize(myrandidx2, DATA_ASSIGN_CORE1);
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

		enable_cycle_counter();
#ifdef PMU_EVENT_CORE1_1
		enable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE1_2
		enable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE1_3
		enable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE1_4
		enable_event_counter(3);
#endif

		/* This is core1, we are slave for the synchronization between cores */
		sync_slave(offset);

		/* Maybe reset the event counters */
#if defined PMU_EVENT_CORE1_1
		/* If any of the event counters is active, then at least the first one
		 * will be active. We can reset the event counters in this case. */
		reset_event_counters();
#endif
		reset_cycle_counter();
		DO_BENCH_CORE1
		disable_cycle_counter();
#ifdef PMU_EVENT_CORE1_1
		disable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE1_2
		disable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE1_3
		disable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE1_4
		disable_event_counter(3);
#endif

		sync_reset();

		xTaskDelay(10);

		cycles = read_cycle_counter();
#ifdef PMU_EVENT_CORE1_1
		event1 = read_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE1_2
		event2 = read_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE1_3
		event3 = read_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE1_4
		event4 = read_event_counter(3);
#endif

		sprintf(&buf[0],
				"Core 1 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				cycles);
		TextOut(Dc, 20, 180, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "CYCLECOUNT label: %s %s %s cores: %d core: 1 cycle_count: %12u iteration: %u offset: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, BENCH_STRING_CORE1, NR_OF_CORES,
				 cycles, iter, offset);

#ifdef PMU_EVENT_CORE1_1
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 1 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE1_1, event1, iter);
#endif
#ifdef PMU_EVENT_CORE1_2
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 2 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE1_2, event2, iter);
#endif
#ifdef PMU_EVENT_CORE1_3
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 3 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE1_3, event3, iter);
#endif
#ifdef PMU_EVENT_CORE1_4
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 4 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE1_4, event4, iter);
#endif

		if (++iter % 100 == 0)
			offset += corenum;
	}
}

void core2(void* pParam) {
	char buf[256];
	HDC Dc = CreateExternalDC(7);
	COLORREF col = 0xFF7F7F7F;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles;
#ifdef PMU_EVENT_CORE2_1
    unsigned int event1;
#endif
#ifdef PMU_EVENT_CORE2_2
    unsigned int event2;
#endif
#ifdef PMU_EVENT_CORE2_3
    unsigned int event3;
#endif
#ifdef PMU_EVENT_CORE2_4
    unsigned int event4;
#endif
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=2;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");
#ifdef PMU_EVENT_CORE2_1
	config_event_counter(0, PMU_EVENT_CORE2_1);
#endif
#ifdef PMU_EVENT_CORE2_2
	config_event_counter(1, PMU_EVENT_CORE2_2);
#endif
#ifdef PMU_EVENT_CORE2_3
	config_event_counter(2, PMU_EVENT_CORE2_3);
#endif
#ifdef PMU_EVENT_CORE2_4
	config_event_counter(3, PMU_EVENT_CORE2_4);
#endif

	while (1) {
#ifdef BENCH_CONFIG_CORE2_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array3);
#endif
#if defined BENCH_CONFIG_CORE2_5 || defined BENCH_CONFIG_CORE2_6
		array_access_randomize(myrandidx3, DATA_ASSIGN_CORE2);
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

		enable_cycle_counter();
#ifdef PMU_EVENT_CORE2_1
		enable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE2_2
		enable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE2_3
		enable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE2_4
		enable_event_counter(3);
#endif

		/* This is core2, we are slave for the synchroniztion between cores */
		sync_slave(offset);

		/* Maybe reset the event counters */
#if defined PMU_EVENT_CORE2_1
		/* If any of the event counters is active, then at least the first one
		 * will be active. We can reset the event counters in this case. */
		reset_event_counters();
#endif
		reset_cycle_counter();
		DO_BENCH_CORE2
		disable_cycle_counter();
#ifdef PMU_EVENT_CORE2_1
		disable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE2_2
		disable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE2_3
		disable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE2_4
		disable_event_counter(3);
#endif

		sync_reset();

		xTaskDelay(10);

		cycles = read_cycle_counter();
#ifdef PMU_EVENT_CORE2_1
		event1 = read_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE2_2
		event2 = read_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE2_3
		event3 = read_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE2_4
		event4 = read_event_counter(3);
#endif

		sprintf(&buf[0],
				"Core 2 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				cycles);
		TextOut(Dc, 20, 280, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "CYCLECOUNT label: %s %s %s cores: %d core: 2 cycle_count: %12u iteration: %u offset: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, BENCH_STRING_CORE2, NR_OF_CORES,
				 cycles, iter, offset);

#ifdef PMU_EVENT_CORE2_1
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 1 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE2_1, event1, iter);
#endif
#ifdef PMU_EVENT_CORE2_2
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 2 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE2_2, event2, iter);
#endif
#ifdef PMU_EVENT_CORE2_3
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 3 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE2_3, event3, iter);
#endif
#ifdef PMU_EVENT_CORE2_4
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 4 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE2_4, event4, iter);
#endif

		if (++iter % 100 == 0)
			offset += corenum;
	}
}

void core3(void* pParam) {
	char buf[256];
	HDC Dc = CreateExternalDC(8);
	COLORREF col = 0xFFFF00FF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles;
#ifdef PMU_EVENT_CORE3_1
    unsigned int event1;
#endif
#ifdef PMU_EVENT_CORE3_2
    unsigned int event2;
#endif
#ifdef PMU_EVENT_CORE3_3
    unsigned int event3;
#endif
#ifdef PMU_EVENT_CORE3_4
    unsigned int event4;
#endif
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=3;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");
#ifdef PMU_EVENT_CORE3_1
	config_event_counter(0, PMU_EVENT_CORE3_1);
#endif
#ifdef PMU_EVENT_CORE3_2
	config_event_counter(1, PMU_EVENT_CORE3_2);
#endif
#ifdef PMU_EVENT_CORE3_3
	config_event_counter(2, PMU_EVENT_CORE3_3);
#endif
#ifdef PMU_EVENT_CORE3_4
	config_event_counter(3, PMU_EVENT_CORE3_4);
#endif

	while (1) {
#ifdef BENCH_CONFIG_CORE3_1
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array4);
#endif
#if defined BENCH_CONFIG_CORE3_5 || defined BENCH_CONFIG_CORE3_6
		array_access_randomize(myrandidx4, DATA_ASSIGN_CORE3);
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

		enable_cycle_counter();
#ifdef PMU_EVENT_CORE3_1
		enable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE3_2
		enable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE3_3
		enable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE3_4
		enable_event_counter(3);
#endif

		/* This is core3, we are slave for the synchroniztion between cores */
		sync_slave(offset);

		/* Maybe reset the event counters */
#if defined PMU_EVENT_CORE3_1
		/* If any of the event counters is active, then at least the first one
		 * will be active. We can reset the event counters in this case. */
		reset_event_counters();
#endif
		reset_cycle_counter();
		DO_BENCH_CORE3
		disable_cycle_counter();
#ifdef PMU_EVENT_CORE3_1
		disable_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE3_2
		disable_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE3_3
		disable_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE3_4
		disable_event_counter(3);
#endif

		sync_reset();

		xTaskDelay(10);

		cycles = read_cycle_counter();
#ifdef PMU_EVENT_CORE3_1
		event1 = read_event_counter(0);
#endif
#ifdef PMU_EVENT_CORE3_2
		event2 = read_event_counter(1);
#endif
#ifdef PMU_EVENT_CORE3_3
		event3 = read_event_counter(2);
#endif
#ifdef PMU_EVENT_CORE3_4
		event4 = read_event_counter(3);
#endif

		sprintf(&buf[0],
				"Core 3 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				cycles);
		TextOut(Dc, 20, 380, &buf[0], strlen(&buf[0]));

		log_info(corenum, buf,
				 "CYCLECOUNT label: %s %s %s cores: %d core: 3 cycle_count: %12u iteration: %u offset: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, BENCH_STRING_CORE3, NR_OF_CORES,
				 cycles, iter, offset);

#ifdef PMU_EVENT_CORE3_1
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 1 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE3_1, event1, iter);
#endif
#ifdef PMU_EVENT_CORE3_2
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 2 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE3_2, event2, iter);
#endif
#ifdef PMU_EVENT_CORE3_3
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 3 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE3_3, event3, iter);
#endif
#ifdef PMU_EVENT_CORE3_4
		log_info(corenum, buf,
				 "EVENTCOUNT label: %s %s cores: %d core: %d pmu: 4 event_number: %#02x event_count: %d iteration: %d\n\r",
				 EXP_LABEL, CONFIG_STRING, NR_OF_CORES,
				 corenum, PMU_EVENT_CORE3_4, event4, iter);
#endif

		if (++iter % 100 == 0)
			offset += corenum;
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


	/* Get information on the implemented events */
	/* uint64_t pmceid0 = read_cei_reg(); */
	/* if (pmceid0 | ARMV8_PMCEID0_L1DC) */
	/* 	log_debug(0, buf, "%s\n\r", "L1 Data cache access event implemented"); */
	/* if (pmceid0 | ARMV8_PMCEID0_L2DC) */
	/* 	log_debug(0, buf, "%s\n\r", "L2 Data cache access event implemented"); */
	/* if (pmceid0 | ARMV8_PMCEID0_L1DCRF) */
	/* 	log_debug(0, buf, "%s\n\r", "L1 Data cache refill event implemented"); */
	/* if (pmceid0 | ARMV8_PMCEID0_L2DCRF) */
	/* 	log_debug(0, buf, "%s\n\r", "L2 Data cache refill event implemented"); */
	/* if (pmceid0 | ARMV8_PMCEID0_L1DCWB) */
	/* 	log_debug(0, buf, "%s\n\r", "L1 Data cache Write-back event implemented"); */
	/* if (pmceid0 | ARMV8_PMCEID0_L2DCWB) */
	/* 	log_debug(0, buf, "%s\n\r", "L2 Data cache Write-back event implemented"); */

	/* log_info(0, buf, "Number of event counters is %d\n\r", read_nr_eventcounters()); */

	/*
	 *	We should never get here, but just in case something goes wrong,
	 *	we'll place the CPU into a safe loop.
	 */
	while (1) {
		log_warning(0, buf, "%s\n\r", "Main program reached safe loop, this should not happen!");
	}
}
