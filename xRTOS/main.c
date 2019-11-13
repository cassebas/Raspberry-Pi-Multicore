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


void task1(void *pParam) {
	HDC Dc = CreateExternalDC(1);
	COLORREF col = 0xFFFF0000;
	int total = 1000;
	int step = 0;
	int dir = 1;
	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}

		DoProgress(Dc, step, total, 10, 100, GetScreenWidth()-20, 20, col);
		xTaskDelay(20);
	}
}

void task2(void *pParam) {
	HDC Dc = CreateExternalDC(2);
	COLORREF col = 0xFF0000FF;
	int total = 1000;
	volatile int step = 0;
	volatile int dir = 1;
	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 200, GetScreenWidth() - 20, 20, col);
		xTaskDelay(22);
	}
}

void task3(void *pParam) {
	HDC Dc = CreateExternalDC(3);
	COLORREF col = 0xFF00FF00;
	int total = 1000;
	int step = 0;
	int dir = 1;
	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 300, GetScreenWidth() - 20, 20, col);
		xTaskDelay(24);
	}
}

void task4 (void* pParam) {
	HDC Dc = CreateExternalDC(4);
	COLORREF col = 0xFFFFFF00;
	int total = 1000;
	int step = 0;
	int dir = 1;
	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 400, GetScreenWidth() - 20, 20, col);
		xTaskDelay(26);
	}
}

void task1A(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(5);
	COLORREF col = 0xFF00FFFF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time, pmcr;
    unsigned int iter=0;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 130, GetScreenWidth() - 20, 20, col);

		pmcr = armv8pmu_pmcr_read();
		cycles_begin = read_counter();
		array_access_linear(mydata);
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		xTaskDelay(35);
		sprintf(&buf[0],
				"Core 0 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 80, &buf[0], strlen(&buf[0]));

		if (step % 10 == 1) {
			sprintf(&buf[0], "Core 0 PMCR: %u Cycle count: %12u iteration: %12u\n\r", pmcr, time, ++iter);
			pl011_uart_puts(buf);
        }
	}
}

void task2A(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(6);
	COLORREF col = 0xFFFFFFFF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time, pmcr;
    unsigned int iter=0;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 230, GetScreenWidth() - 20, 20, col);

		pmcr = armv8pmu_pmcr_read();
		cycles_begin = read_counter();
		array_access_linear(mydata);
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		xTaskDelay(37);
		sprintf(&buf[0],
				"Core 1 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 180, &buf[0], strlen(&buf[0]));

		if (step % 10 == 2) {
			sprintf(&buf[0], "Core 1 PMCR: %u Cycle count: %12u iteration: %u\n\r", pmcr, time, ++iter);
			pl011_uart_puts(buf);
        }
	}
}

void task3A(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(7);
	COLORREF col = 0xFF7F7F7F;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time, pmcr;
    unsigned int iter=0;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;
		}
		DoProgress(Dc, step, total, 10, 330, GetScreenWidth() - 20, 20, col);

		pmcr = armv8pmu_pmcr_read();
		cycles_begin = read_counter();
		array_access_linear(mydata);
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		xTaskDelay(39);
		sprintf(&buf[0],
				"Core 2 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 280, &buf[0], strlen(&buf[0]));

		if (step % 10 == 3) {
			sprintf(&buf[0], "Core 2 PMCR: %u Cycle count: %12u iteration: %u\n\r", pmcr, time, ++iter);
			pl011_uart_puts(buf);
        }
	}
}

void task4A(void* pParam) {
	char buf[32];
	HDC Dc = CreateExternalDC(8);
	COLORREF col = 0xFFFF00FF;
	int total = 1000;
	int step = 0;
	int dir = 1;
    unsigned int cycles_begin, cycles_end, time, pmcr;
    unsigned int iter=0;
	enable_counters();

	// Initialize the array for the synthetic benchmark
	volatile bigstruct_t mydata[SYNBENCH_DATASIZE];

	while (1) {
		step += dir;
		if ((step == total) || (step == 0))
		{
			dir = -dir;

		}
		DoProgress(Dc, step, total, 10, 430, GetScreenWidth() - 20, 20, col);

		pmcr = armv8pmu_pmcr_read();
		cycles_begin = read_counter();
		array_access_linear(mydata);
		cycles_end = read_counter();
		time = cycles_end - cycles_begin;

		xTaskDelay(41);
		sprintf(&buf[0],
				"Core 3 Load: %3i%% Task count: %2i Cycle count: %12u",
				xLoadPercentCPU(),
				xTaskGetNumberOfTasks(),
				time);
		TextOut(Dc, 20, 380, &buf[0], strlen(&buf[0]));

		if (step % 10 == 4) {
			sprintf(&buf[0], "Core 3 PMCR: %u Cycle count: %12u iteration: %u\n\r", pmcr, time, ++iter);
			pl011_uart_puts(buf);
        }
	}
}


void main (void)
{
	Init_EmbStdio(WriteText);										// Initialize embedded stdio
	PiConsole_Init(0, 0, 0, printf);								// Auto resolution console, message to screen
	displaySmartStart(printf);										// Display smart start details
	ARM_setmaxspeed(printf);										// ARM CPU to max speed
	printf("Task tick rate: %u\n", configTICK_RATE_HZ);

    unsigned int baudrate = 115200;
    if (pl011_uart_init(baudrate)) {
        printf("UART succesfully initialized\n");
        pl011_uart_puts("UART succesfully initialized\n\0");
    } else {
        printf("UART could not be initialized!\n");
    }
    pl011_uart_puts("Initializing xRTOS\n");

	xRTOS_Init();													// Initialize the xRTOS system .. done before any other xRTOS call

	/* Core 0 tasks */
	xTaskCreate(0, task1, "Core0-1", 512, NULL, 4, NULL);
	xTaskCreate(0, task1A, "Core0-2", 512, NULL, 2, NULL);

	/* Core 1 tasks */
	xTaskCreate(1, task2, "Core1-1", 512, NULL, 2, NULL);
	xTaskCreate(1, task2A, "Core1-2", 512, NULL, 2, NULL);
	
	/* Core 2 tasks */
	xTaskCreate(2, task3, "Core2-1", 512, NULL, 2, NULL);
	xTaskCreate(2, task3A, "Core2-2", 512, NULL, 2, NULL);

	/* Core 3 tasks */
	xTaskCreate(3, task4, "Core3-1", 512, NULL, 2, NULL);
	xTaskCreate(3, task4A, "Core3-2", 512, NULL, 2, NULL);

	/* Start scheduler */
	xTaskStartScheduler();
	/*
	 *	We should never get here, but just in case something goes wrong,
	 *	we'll place the CPU into a safe loop.
	 */
	while (1) {
	}
}
