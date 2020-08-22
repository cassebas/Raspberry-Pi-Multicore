#include "xRTOS.h"
#include "mutex.h"
#include "semaphore.h"
#include "corunners_definition.h"

#ifdef MMU_ENABLE
static SemaphoreHandle_t sem[NR_OF_LOCKS];
#else
// single writer/multiple reader (SWMR) atomic register level
// for Peterson's algorithm
static volatile int level[NR_OF_LOCKS][MAX_CPU_CORES] = {0};
static volatile int last_to_enter[NR_OF_LOCKS][MAX_CPU_CORES] = {0};
#endif

void init_lock(int lock_number)
{
#ifdef MMU_ENABLE
	// Initialize the semaphore for protection of a critical section
	sem[lock_number] = xSemaphoreCreateBinary();
#endif
}

void lock(int lock_number, int corenum)
{
#ifdef MMU_ENABLE
	/* We'll make a lock by using a semaphore */
	xSemaphoreTake(sem[lock_number]);
#else
	/*
	 * We'll make a lock according to a variation of Peterson's algorithm: the
	 * Filter algorithm. This makes sure that the actual printing is done within
	 * a critical section.
	 */
	int k;
	bool higher_level;
	for (int l=1; l<NR_OF_CORES; l++) {
		level[lock_number][corenum] = l;
		last_to_enter[lock_number][l] = corenum;
		higher_level = true;
		while ((last_to_enter[lock_number][l] == corenum) && higher_level) {
			k = 0;
			higher_level = false;
			while (!higher_level && k < NR_OF_CORES) {
				if (k != corenum)
					higher_level = (level[lock_number][k] >= l);
				k++;
			}
		}
	}
#endif
}

void unlock(int lock_number, int corenum)
{
#ifdef MMU_ENABLE
	// release lock
	xSemaphoreGive(sem[lock_number]);
#else
	// release lock
	level[lock_number][corenum] = 0;
#endif
}
