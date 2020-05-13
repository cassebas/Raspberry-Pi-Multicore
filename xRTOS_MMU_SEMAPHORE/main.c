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
#define NR_OF_CORES 2
#define BENCH_CONFIG_CORE0_1
#define BENCH_CONFIG_CORE1_5
#define CONFIG_STRING "configuration: '15'"

#define BENCH_STRING_CORE0 "benchmark: malardalen_bsort100"
#define BENCH_STRING_CORE1 "benchmark: random_array_access"
#define BENCH_STRING_CORE2 ""
#define BENCH_STRING_CORE3 ""

#define BENCH_ARG_CORE0 Array1
#define BENCH_ARG_CORE1 mydata2, myrandidx2
#define BENCH_ARG_CORE2 
#define BENCH_ARG_CORE3 

#define DO_BENCH_CORE0 bsort100_BubbleSort(BENCH_ARG_CORE0);
#define DO_BENCH_CORE1 array_access_random(BENCH_ARG_CORE1);
#define DO_BENCH_CORE2 
#define DO_BENCH_CORE3 


#define EXP_LABEL "DEBUG_BENCH_15"


/**
 * Maybe define the needed datastructures (depending on
 * the specific configuration of benchmarks).
 */
int Array1[MAXDIM];
volatile bigstruct_t mydata2[SYNBENCH_DATASIZE];
volatile int myrandidx2[SYNBENCH_DATASIZE];

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


void heartbeat(void* pParam)
{
	uint8_t* gpio = (uint8_t*) pParam;
	bool ok = gpio_setup(*gpio, GPIO_OUTPUT);
	while (ok) {
		gpio_output(*gpio, 1);
		xTaskDelay(configTICK_RATE_HZ);
		gpio_output(*gpio, 0);
		xTaskDelay(configTICK_RATE_HZ);
	}
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
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=0;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");

	while (1) {
		/* Maybe initialize the bsort100 array with random nrs (each iteration) */
		bsort100_Initialize(Array1);

		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 100, GetScreenWidth()-20, 20, col);

		/* Master gets to invalidate the complete cache */
		invalidate_cache();

		enable_cycle_counter();

		/* /\* This is core0, we are master for the synchronization between cores *\/ */
		/* sync_master(); */

		reset_cycle_counter();
		bsort100_BubbleSort(Array1);
		disable_cycle_counter();

		/* sync_reset(); */

		xTaskDelay(10);

		cycles = read_cycle_counter();

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
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=1;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");

	while (1) {
		array_access_initialize(mydata2);
		array_access_randomize(myrandidx2, 1);
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 200, GetScreenWidth() - 20, 20, col);

		/* Slave only invalidates its own L1 cache */
		invalidate_data_cache(1);

		enable_cycle_counter();

		/* /\* This is core1, we are slave for the synchronization between cores *\/ */
		/* sync_slave(offset); */

		/* Maybe reset the event counters */
		reset_cycle_counter();
		array_access_random(mydata2, myrandidx2);
		disable_cycle_counter();

		/* sync_reset(); */

		xTaskDelay(10);

		cycles = read_cycle_counter();

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
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=2;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 300, GetScreenWidth() - 20, 20, col);

		/* Slave only invalidates its own L1 cache */
		invalidate_data_cache(1);

		enable_cycle_counter();

		/* /\* This is core2, we are slave for the synchroniztion between cores *\/ */
		/* sync_slave(offset); */

		/* Maybe reset the event counters */
#if defined PMU_EVENT_CORE2_1
		/* If any of the event counters is active, then at least the first one
		 * will be active. We can reset the event counters in this case. */
		reset_event_counters();
#endif
		reset_cycle_counter();
		disable_cycle_counter();

		/* sync_reset(); */

		xTaskDelay(10);

		cycles = read_cycle_counter();

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
    unsigned int iter=1;
    unsigned int offset=0;
	int corenum=3;

	/* Globally enable PMU */
	enable_pmu();

	log_debug(0, buf, "%s\n\r", "config pmu_events");

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;

		}
		DoProgress(Dc, step, total, 10, 400, GetScreenWidth() - 20, 20, col);

		/* Slave only invalidates its own L1 cache */
		invalidate_data_cache(1);

		enable_cycle_counter();

		/* /\* This is core3, we are slave for the synchroniztion between cores *\/ */
		/* sync_slave(offset); */

		/* Maybe reset the event counters */
		reset_cycle_counter();
		disable_cycle_counter();

		/* sync_reset(); */

		xTaskDelay(10);

		cycles = read_cycle_counter();

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

	/* Core 0 task */
	xTaskCreate(0, core0, "Core0", 512, NULL, 2, NULL);

	/* Core 1 task */
	xTaskCreate(1, core1, "Core1", 512, NULL, 2, NULL);

	uint8_t gpio3 = 5;
	void* gpio3_ptr = (void*) &gpio3;
	xTaskCreate(2, heartbeat, "HEARTBEAT", 512, gpio3_ptr, 2, NULL);

	uint8_t gpio4 = 12;
	void* gpio4_ptr = (void*) &gpio4;
	xTaskCreate(3, heartbeat, "HEARTBEAT", 512, gpio4_ptr, 2, NULL);

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
