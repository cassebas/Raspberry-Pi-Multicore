#include <stdint.h>
#include <string.h>
#include "rpi-smartstart.h"
#include "emb-stdio.h"
#include "xRTOS.h"
#include "task.h"
#include "windows.h"

/* definition of performance monitor control registers and such */
#include "armv8_pm.h"
/* our own synthetic benchmark for testing purposes */
#include "synthetic_bench.h"
#include "malardalen.h"

/* For Mälardalen bsort100 benchmark */
int Array1[MAXDIM];
int Array2[MAXDIM];
int Array3[MAXDIM];
int Array4[MAXDIM];

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


void core0(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(5);
	COLORREF col = 0xFF00FFFF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=0;
	RegType_t ostick;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 100, GetScreenWidth()-20, 20, col);

		/* This is core0, we are master for the synchroniztion between cores */
		sync_master();

		ostick = getOSTickCounter();
		cycles_begin = read_counter();
		// array_access_linear(mydata);
		bsort100_BubbleSort(Array1);
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

		log_info(0, buf,
				 "Core 0 OSTick: %u Cycle count: %12u iteration: %u\n\r",
				 ostick, time, ++iter);
	}
}

void core1(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(6);
	COLORREF col = 0xFFFFFFFF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=0;
	RegType_t ostick;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 200, GetScreenWidth() - 20, 20, col);

		/* This is core1, we are slave for the synchronization between cores */
		sync_slave(0);

		ostick = getOSTickCounter();
		cycles_begin = read_counter();
		// array_access_linear(mydata);
		bsort100_BubbleSort(Array2);
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

		log_info(1, buf,
				 "Core 1 OSTick: %u Cycle count: %12u iteration: %u\n\r",
				 ostick, time, ++iter);
	}
}

void core2(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(7);
	COLORREF col = 0xFF7F7F7F;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=0;
	RegType_t ostick;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 300, GetScreenWidth() - 20, 20, col);

		/* This is core2, we are slave for the synchroniztion between cores */
		sync_slave(0);

		ostick = getOSTickCounter();
		cycles_begin = read_counter();
		// array_access_linear(mydata);
		bsort100_BubbleSort(Array3);
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

		log_info(2, buf,
				 "Core 2 OSTick: %u Cycle count: %12u iteration: %u\n\r",
				 ostick, time, ++iter);
	}
}

void core3(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(8);
	COLORREF col = 0xFFFF00FF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time;
    unsigned int iter=0;
	RegType_t ostick;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;

		}
		DoProgress(Dc, step, total, 10, 400, GetScreenWidth() - 20, 20, col);

		/* This is core3, we are slave for the synchroniztion between cores */
		sync_slave(0);

		ostick = getOSTickCounter();
		cycles_begin = read_counter();
		// array_access_linear(mydata);
		bsort100_BubbleSort(Array4);
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

		log_info(3, buf,
				 "Core 3 OSTick: %u Cycle count: %12u iteration: %u\n\r",
				 ostick, time, ++iter);
	}
}


void main (void)
{
	char buf[32];

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
        log_info(0, buf, "%s\n\r", "UART succesfully initialized");
    } else {
        printf("UART could not be initialized!\n");
        log_warning(0, buf, "%s\n\r", "UART could not be initialized!");
    }

    log_info(0, buf, "%s\n\r", "Initializing xRTOS");
	xRTOS_Init();													// Initialize the xRTOS system .. done before any other xRTOS call

	/* Initialize the bsort100 arrays */
	bsort100_Initialize(Array1);
	bsort100_Initialize(Array2);
	bsort100_Initialize(Array3);
	bsort100_Initialize(Array4);

	/* Core 0 task */
	xTaskCreate(0, core0, "Core0", 512, NULL, 2, NULL);

	/* Core 1 task */
	xTaskCreate(1, core1, "Core1", 512, NULL, 2, NULL);
	
	/* Core 2 task */
	xTaskCreate(2, core2, "Core2", 512, NULL, 2, NULL);

	/* Core 3 task */
	xTaskCreate(3, core3, "Core3", 512, NULL, 2, NULL);

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
