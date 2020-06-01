#include <stdint.h>
#include "xRTOS.h"
#include "rpi-smartstart.h"
#include "task.h"
#include <stdio.h>
#include <stdarg.h>
#include "debug.h"

#ifdef MMU_ENABLE
#include "semaphore.h"
#include "mmu.h"
#endif

/*
 * Macros used by vListTask to indicate which state a task is in.
 */
#define tskRUNNING_CHAR		( 'X' )
#define tskBLOCKED_CHAR		( 'B' )
#define tskREADY_CHAR		( 'R' )
#define tskDELETED_CHAR		( 'D' )
#define tskSUSPENDED_CHAR	( 'S' )


/* The name allocated to the Idle task */
#ifndef configIDLE_TASK_NAME
	#define configIDLE_TASK_NAME "IDLE"
#endif

/* The name allocated to the HEARTBEAT task */
#ifndef configHEARTBEAT_TASK_NAME
	#define configHEARTBEAT_TASK_NAME "HEARTBEAT"
#endif

#define CoreEnterCritical DisableInterrupts
#define CoreExitCritical EnableInterrupts
#define ImmediateYield __asm volatile ("svc 0")

#ifdef MMU_ENABLE
static SemaphoreHandle_t screenSem;
#endif

// single writer/multiple reader (SWMR) atomic register level
// for Peterson's algorithm
static volatile int level[MAX_CPU_CORES] = {0};
static volatile int last_to_enter[MAX_CPU_CORES] = {0};


typedef struct TaskControlBlock* task_ptr;

/*--------------------------------------------------------------------------}
{						 TASK LIST STRUCTURE DEFINED						}
{---------------------------------------------------------------------------}
.  A task list is a simple double link list of tasks. Each task control
.  block conatins a prev and next pointer. Starting at the head task in the 
.  list structure and moving thru each task next pointer you will arrive at
.  the tail pointer in the list being the last task. The head, tail values
.  will be NULL for a no task situation. The moment you have a task in list
.  head->prev will be NULL and tail->next will be NULL as error checking.
.--------------------------------------------------------------------------*/
typedef struct tasklist
{
	struct TaskControlBlock* head;								/*< Head entry for task list */
	struct TaskControlBlock* tail;								/*< Tail entry for task list */
} TASK_LIST_t;


/*--------------------------------------------------------------------------}
{				 TASK CONTROL BLOCK STRUCTURE DEFINED						}
{---------------------------------------------------------------------------}
.  A task control block (TCB) is allocated for each task, and stores task  
.  state information, including a pointer to the task's context (the task's 
.  run time environment and data, including all register values)     
.--------------------------------------------------------------------------*/
typedef struct TaskControlBlock 
{
	volatile RegType_t	*pxTopOfStack;							/*< Points to the location of the last item placed on the tasks stack.
																	THIS MUST BE THE FIRST MEMBER OF THE TCB STRUCT AND MUST BE VOLATILE.
																	It changes each task switch and the optimizer needs to know that */
	struct pxTaskFlags_t {
		volatile RegType_t	uxCriticalNesting : 8;				/*< Holds the critical section nesting depth */
		volatile RegType_t	uxTaskUsesFPU : 1;					/*< If task uses FPU this flag will be set to 1 and FPU registers save on context switch */
		RegType_t			_reserved : (sizeof(RegType_t) * 8) - 9;
	}	pxTaskFlags;											/*< Task flags ... these flags will be save FPU, nested count etc in future
																	THIS MUST BE THE SECOND MEMBER OF THE TCB STRUCT AND MUST BE VOLATILE.
																	It changes each task switch and the optimizer needs to know that */

	RegType_t* pxStack;											/*< Points to the start of the stack allocated when task created */

	/* These form the task state double link list system */
	struct TaskControlBlock* next;								/*< Next task in list */
	struct TaskControlBlock* prev;								/*< Prev task in list */
	/* If task is in the delayed list this is release time */
	RegType_t ReleaseTime;										/*< Core OSTickCounter at which task will be released from delay */

#ifdef MMU_ENABLE
	SemaphoreHandle_t taskSem;									/*< Task semaphore */
#endif

	struct {
		RegType_t		uxPriority : 8;							/*< The priority of the task.  0 is the lowest priority. */
		RegType_t		taskState : 8;							/*< Task state running, delayed, blocked etc */
		RegType_t		_reserved : (sizeof(RegType_t)*8) - 20;
		RegType_t		assignedCore : 3;						/*< Core this task is assigned to on a multicore, always 0 on single core */
		RegType_t		inUse : 1;								/*< This task is in use field */
	};
	
	char				pcTaskName[ configMAX_TASK_NAME_LEN ];	/*< Descriptive name given to task when created.  Facilitates debugging only. */ 
} TCB_t;


/*--------------------------------------------------------------------------}
{				 CORE CONTROL BLOCK STRUCTURE DEFINED						}
{---------------------------------------------------------------------------}
.  A CPU control block (coreCB) is allocated for each CPU core and stores 
.  information, specific to the tasks being run on that CPU core.
.--------------------------------------------------------------------------*/
static struct CoreControlBlock
{
	volatile TCB_t* pxCurrentTCB;							/*< Points to the current task that is running on this CPU core.
																THIS MUST BE THE FIRST MEMBER OF THE CORE CONTROL BLOCK STRUCT AND MUST BE VOLATILE.
																It changes each task switch and the optimizer needs to know that */
	TaskHandle_t xIdleTaskHandle;							/*< Holds the handle of the core idle task. The idle task is created automatically when the scheduler is started. */
	TASK_LIST_t readyTasks;									/*< List of tasks that are ready to run */
	TASK_LIST_t delayedTasks;								/*< List of tasks that are in delayed state */
	RegType_t OSTickCounter;								/*< Incremented each tick timer - Used in delay and timeout functions */
	struct TaskControlBlock coreTCB[MAX_TASKS_PER_CORE];	/*< This cores list of tasks on the core */
	struct {
		volatile unsigned uxCurrentNumberOfTasks : 16;		/*< Current number of task running on this core */
		volatile unsigned uxPercentLoadCPU : 16;			/*< Last CPU load calculated = uxIdleTickCount/configTICK_RATE_HZ * 100 in percent for last 1 sec frame   */
		volatile unsigned uxIdleTickCount : 16;			    /*< Current ticks in 1 sec analysis frame that idle was current task */
		volatile unsigned uxCPULoadCount: 16;				/*< Current count in 1 sec analysis frame .. one sec =  configTICK_RATE_HZ ticks */
		volatile unsigned uxSchedulerSuspended : 16;		/*< Context switches are held pending while the scheduler is suspended.  */
		unsigned xSchedulerRunning : 1;						/*< Set to 1 if the scheduler is running on this core */
		unsigned xCoreBlockInitialized : 1;					/*< Set to 1 if the core block has been initialized */
		/* /\* Synchronization mechanism for agreeing to start on specific OSTickCounter value *\/ */
		/* unsigned OSTickStart; */
		/* Synchronization mechanism for agreeing to start at the same time */
		volatile unsigned CoreState : 3;
		volatile unsigned SyncScheduler : 1;
		volatile unsigned SyncOffset;
	};
} coreCB[MAX_CPU_CORES] = { 0 };

/***************************************************************************}
{					   PRIVATE INTERNAL DATA STORAGE					    }
****************************************************************************/

static RegType_t TestStack[16384] __attribute__((aligned(16)));
static RegType_t* TestStackTop = &TestStack[16384];

static uint64_t m_nClockTicksPerHZTick = 0;							// Divisor to generat tick frequency

/***************************************************************************}
{					    PRIVATE INTERNAL ROUTINES						    }
****************************************************************************/

/*--------------------------------------------------------------------------}
{			Adds the task into the task double linked list					}
{--------------------------------------------------------------------------*/
static void AddTaskToList (TASK_LIST_t* list, struct TaskControlBlock* task)
{
	if (list->tail != 0)											// List already has at least one task
	{
		/* Insert task into double linked ready list */
		list->tail->next = task;									// Add task to current list tail
		task->prev = list->tail;									// Set task prev to current lits tail
		list->tail = task;											// Now task becomes the list tail
		task->next = 0;												// Zero the task nextready pointer
	}
	else {															// No existing tasks in list
		/* Init ready list */
		list->tail = task;											// Task is the tail
		list->head = task;											// Task is also head
		task->next = 0;												// Task has no next ready
		task->prev = 0;												// Task has no prev ready
	}
}

/*--------------------------------------------------------------------------}
{				Removes the task from task double linked list				}
{--------------------------------------------------------------------------*/
static void RemoveTaskFromList (TASK_LIST_t* list, struct TaskControlBlock* task)
{
	if (task == list->head)											// Task is the first one in the list		
	{
		if (task == list->tail)										// If task is also the last one on list it is only task in list
		{
			list->tail = 0;											// Zero the tail task ptr
			list->head = 0;											// Zero the head task ptr
		}
		else {
			list->head = task->next;								// Move next task up to list head position
			list->head->prev = 0;									// This task is now top its previous is then null (it would have been the task we are removing)
		}
	}
	else {															// Task is not head then must be in list
		if (task == list->tail)										// Is task the tail ptr in list
		{
			list->tail = task->prev;								// List tail will now become tasks previous 
			list->tail->next = 0;									// Zero that tasks next pointer (it would have been the task we are removing)
		}
		else {
			task->next->prev = task->prev;							// Our next prev will point to our prev (unchains task from next links)
			task->prev->next = task->next;							// Our prev next will point to our next (unchains task from prev links)
		}
	}
}

/*--------------------------------------------------------------------------}
{				The default idle task .. that does nothing :-)				}
{--------------------------------------------------------------------------*/
static void prvIdleTask(void* pvParameters)
{
	/* Stop warnings. */
	(void)pvParameters;

	/** THIS IS THE RTOS IDLE TASK - WHICH IS CREATED AUTOMATICALLY WHEN THE
	SCHEDULER IS STARTED. **/
	for (;; )
	{

	}
}

/*--------------------------------------------------------------------------}
{			Starts the tasks running on the core just as it says			}
{--------------------------------------------------------------------------*/
static void StartTasksOnCore(void)
{
#ifdef MMU_ENABLE
	MMU_enable();													// Enable MMU
#endif
	EL0_Timer_Set(m_nClockTicksPerHZTick);							// Set the EL0 timer
	EL0_Timer_Irq_Setup();											// Setup the EL0 timer interrupt

#ifndef MMU_ENABLE
	EnableInterrupts();												// Enable interrupts on core
#endif
	xStartFirstTask();												// Restore context starting the first task
}

/***************************************************************************}
{					    PUBLIC INTERFACE ROUTINES						    }
****************************************************************************/

/*-[xRTOS_Init]-------------------------------------------------------------}
.  Initializes xRTOS system and must be called before any other xRTOS call
.--------------------------------------------------------------------------*/
void xRTOS_Init (void)
{
	for (int i = 0; i < MAX_CPU_CORES; i++)
	{
		RPi_coreCB_PTR[i] = &coreCB[i];								// Set the core block pointers in the smartstart system needed by irq and swi vectors
		coreCB[i].xCoreBlockInitialized = 1;						// Set the core block initialzied flag to state this has been done

		// Initialize the states of the cores to inactive. If a core is started
		// by task creation, its state will be set to active.
		coreCB[i].CoreState = INACTIVE;
		coreCB[i].SyncScheduler = 0;
		coreCB[i].SyncOffset = 0;
	}

#ifdef MMU_ENABLE
	// Initialize the semaphore for protection of a critical section
	screenSem = xSemaphoreCreateBinary();
#endif
}

/*-[ xTaskCreate ]----------------------------------------------------------}
.  Creates an xRTOS task on the given core.
.--------------------------------------------------------------------------*/
void xTaskCreate (uint8_t corenum,									// The core number to run task on
				  void (*pxTaskCode) (void* pxParam),				// The code for the task
				  const char * const pcName,						// The character string name for the task
				  const unsigned int usStackDepth,					// The stack depth in register size for the task stack
				  void * const pvParameters,						// Private parameter that may be used by the task
				  uint8_t uxPriority,								// Priority of the task
				  TaskHandle_t* const pxCreatedTask)				// A pointer to return the task handle (NULL if not required)
{
	char buf[32];
	int i;
	for (i = 0; (i < MAX_TASKS_PER_CORE) && (coreCB[corenum].coreTCB[i].inUse != 0); i++) {};
	if (i < MAX_TASKS_PER_CORE)
	{
		struct CoreControlBlock* cb;
		struct TaskControlBlock* task;
		CoreEnterCritical();										// Entering core critical area	
		cb = &coreCB[corenum];										// Set pointer to core block
		task = &cb->coreTCB[i];										// This is the task we are talking about
		task->pxStack = TestStackTop;								// Hold the top of task stack
		task->pxTopOfStack = taskInitialiseStack(TestStackTop, pxTaskCode, pvParameters);
		task->pxTaskFlags = (struct pxTaskFlags_t){ 0 };			// Make sure the task flags are clear
		TestStackTop -= usStackDepth;
		task->uxPriority = uxPriority;								// Hold the task priority
		task->inUse = 1;											// Set the task is in use flag
		task->assignedCore = corenum;								// Hold the core number task assigned to
#ifdef MMU_ENABLE
		task->taskSem = xSemaphoreCreateBinary();					// Create a semaphore
#endif

		if (pcName) {
			int j;
			for (j = 0; (j < configMAX_TASK_NAME_LEN - 1) && (pcName[j] != 0); j++)
				task->pcTaskName[j] = pcName[j];					// Transfer the taskname
			task->pcTaskName[j] = 0;								// Make sure asciiz
		}
		cb->uxCurrentNumberOfTasks++;								// Increment task count on core
		if (cb->pxCurrentTCB == 0) cb->pxCurrentTCB = task;			// If current task on core make this the current
		task->taskState = tskREADY_CHAR;							// Set the read char state
		AddTaskToList(&cb->readyTasks, task);						// Add task to read task lits
		if (pxCreatedTask) (*pxCreatedTask) = task;

		if (strcmp(pcName, configIDLE_TASK_NAME) != 0) {
			if (strcmp(pcName, configHEARTBEAT_TASK_NAME) != 0) {
				// Set the core's state to active
				log_debug(corenum, buf,
						  "Setting state to active core=%d task name=%s\n\r",
						  corenum, pcName);
				cb->CoreState = ACTIVE;
			}
		}

		CoreExitCritical();											// Exiting core critical area
	}
}

/*-[ xTaskDelay ]-----------------------------------------------------------}
.  Moves an xRTOS task from the ready task list into the delayed task list
.  until the time wait in timer ticks is expired. This effectively stalls
.  any task processing at that time for the fixed period of time.
.--------------------------------------------------------------------------*/
void xTaskDelay (const unsigned int time_wait)
{
	if (time_wait)													// Non zero wait time requested
	{
		struct TaskControlBlock* task;
		unsigned int corenum = getCoreID();							// Get the core ID
		struct CoreControlBlock* cb = &coreCB[corenum];				// Set pointer to core block
#ifndef MMU_ENABLE
		CoreEnterCritical();										// Entering core critical area
#endif
		task = (struct TaskControlBlock*) cb->pxCurrentTCB;			// Set temp task pointer .. typecast is to stop volatile dropped warning
#ifdef MMU_ENABLE
		xSemaphoreTake(task->taskSem);								// We are going to play with list lock the task semaphore
#endif
		task->ReleaseTime = cb->OSTickCounter + time_wait;			// Calculate release tick value
		RemoveTaskFromList(&cb->readyTasks, task);					// Remove task from ready list
		task->taskState = tskBLOCKED_CHAR;							// Change task state to blocked
		AddTaskToList(&cb->delayedTasks, task);						// Add the task to delay list
#ifdef MMU_ENABLE
		xSemaphoreGive(task->taskSem);								// Okay clear to release task semaphore
#else
		CoreExitCritical();
#endif
		ImmediateYield;												// Immediate yield ... store task context, reschedule new current task and switch to it
	}
}

/*-[ xTaskStartScheduler ]--------------------------------------------------}
.  starts the xRTOS task scheduler effectively starting the whole system
.--------------------------------------------------------------------------*/
void xTaskStartScheduler( void )
{
	/* Add the idle task at the lowest priority to each core */
	for (int i = 0; i < MAX_CPU_CORES; i++)
	{
		xTaskCreate(i, prvIdleTask,	configIDLE_TASK_NAME,
			configMINIMAL_STACK_SIZE, 0, tskIDLE_PRIORITY, 
			&coreCB[i].xIdleTaskHandle); 
	}

	/* Calculate divisor to create Timer Tick frequency on EL0 timer */
	m_nClockTicksPerHZTick = (EL0_Timer_Frequency() / configTICK_RATE_HZ);

#ifdef MMU_ENABLE
	/* MMU table setup done by core 0 */
	MMU_setup_pagetable();
#endif

	/* Start each core in reverse order because core0 is running this code  */
	CoreExecute(3, StartTasksOnCore);								// Start tasks on core3
	CoreExecute(2, StartTasksOnCore);								// Start tasks on core2
	CoreExecute(1, StartTasksOnCore);								// Start tasks on core1
	StartTasksOnCore();												// Start tasks on core0
}

/*-[ xTaskGetNumberOfTasks ]------------------------------------------------}
.  Returns the number of xRTOS tasks assigned to the core this is called
.--------------------------------------------------------------------------*/
unsigned int xTaskGetNumberOfTasks (void )
{
	return coreCB[getCoreID()].uxCurrentNumberOfTasks;				// Return number of tasks on current core
}

/*-[ xLoadPercentCPU ]------------------------------------------------------}
.  Returns the load on the core this is called from in percent (0 - 100)
.--------------------------------------------------------------------------*/
unsigned int xLoadPercentCPU (void)
{
	return (((configTICK_RATE_HZ - coreCB[getCoreID()].uxPercentLoadCPU) * 100) / configTICK_RATE_HZ);
}


/*
 * Called from the real time kernel tick via the EL0 timer irq this increments 
 * the tick count and checks if any tasks that are blocked for a finite period 
 * required removing from a delayed list and placing on the ready list.
 */
void xTaskIncrementTick (void)
{
	struct CoreControlBlock* ccb = &coreCB[getCoreID()];

	if (ccb->xCoreBlockInitialized == 1)							// Check the core block is initialized  
	{
		if (ccb->uxSchedulerSuspended == 0)							// Core scheduler not suspended
		{

			/* LdB - Addition to calc CPU Load */
			if (ccb->pxCurrentTCB == ccb->xIdleTaskHandle)			// Is the core current task the core idle task
			{
				ccb->uxIdleTickCount++;								// Inc idle tick count in the current 1 second analysis frame
			}
			if (ccb->uxCPULoadCount >= configTICK_RATE_HZ)			// If configTICK_RATE_HZ ticks done, time to see how many were idle
			{
				ccb->uxCPULoadCount = 0;							// Zero the config count for next analysis process period to start again
				ccb->uxPercentLoadCPU = ccb->uxIdleTickCount;		// Transfer the idletickcount to uxPercentLoadCPU we will only do calc when asked
				ccb->uxIdleTickCount = 0;							// Zero the idle tick count
			}
			else ccb->uxCPULoadCount++;								// Increment the process tick count

			/* Increment timer tick and check delaytasks for timeout */
			ccb->OSTickCounter++;									// Increment OS tick counter
			struct TaskControlBlock* task = ccb->delayedTasks.head;	// Set task to delay head
			while (task != 0)
			{
				if (ccb->OSTickCounter >= task->ReleaseTime)		// Check if release time is up
				{
					RemoveTaskFromList(&ccb->delayedTasks, task);	// Remove the task from delay list
					task->taskState = tskREADY_CHAR;				// Set the read char state
					AddTaskToList(&ccb->readyTasks, task);			// Add the task to the ready list
				}
				task = task->next;									// Next delayed task
			}
		}
	}
}


/*
 * Simple round robin scheduler on tasks that are in the readyTasks list
 */
void xSchedule (void)
{
	int coreID = getCoreID();
	struct CoreControlBlock* ccb = &coreCB[coreID];			// Pointer to core control block
	if (ccb->xCoreBlockInitialized == 1)							// Check the core block is initialized  
	{
		if (ccb->uxSchedulerSuspended == 0)							// Core scheduler not suspended
		{
			struct TaskControlBlock* next = ccb->pxCurrentTCB->next;
			// Check current task has a next ready task with same or higher prio
			while (next && ccb->pxCurrentTCB->uxPriority > next->uxPriority)
				next = next->next;

			if (next)
				ccb->pxCurrentTCB = next;						// Simply load next ready
			else
				ccb->pxCurrentTCB = ccb->readyTasks.head;		// No next ready so load readyTasks head

			// CT: in our situation, the head will always be the 'Core' task.
			// But we'll leave the code above just as it is for now.
			// Here comes the synchronization mechanism.
			if (ccb->SyncScheduler) {
				if (coreID == 0) {
					// we are master
					if (ccb->CoreState == ACTIVE)
						ccb->CoreState = WAITING;
					else if (ccb->CoreState == WAITING)
						ccb->CoreState = TIMER_SET;
					else if (ccb->CoreState == TIMER_SET)
						ccb->CoreState = RUNNING;
					else if (ccb->CoreState == RUNNING)
						ccb->CoreState = ACTIVE;
					ccb->SyncScheduler = 0;
				} else {
					// we are slave
					if (ccb->CoreState == TIMER_SET) {
						if (ccb->SyncOffset > 0)
							ccb->SyncOffset--;
						else {
							ccb->CoreState = RUNNING;
							ccb->SyncScheduler = 0;
						}
					} else {
						char buf[32];
						log_debug(coreID, buf,
								  "Slave in scheduler sync mechanism, state == %s\n\r",
								  ccb->CoreState);
					}
				}
			}
		}
	}
}

/*
 *	This is the TICK interrupt service routine, note. no SAVE/RESTORE_CONTEXT here
 *	as thats done in the bottom-half of the ISR in assembler.
 */
void xTickISR(void)
{
	xTaskIncrementTick();											// Run the timer tick
	xSchedule();													// Run scheduler selecting next task 
	EL0_Timer_Set(m_nClockTicksPerHZTick);							// Set EL0 timer again for timer tick period
}

void sync_master()
{
	char buf[32];
	int coreID = getCoreID();
	struct CoreControlBlock* ccb = &coreCB[coreID];
	struct CoreControlBlock* ccbslave;
	int sync_ready;

	log_debug(coreID, buf, "Master starting synchronization - core ID=%d\n\r", coreID);

	// Notify the scheduler that we're ready for synchronization
	ccb->SyncScheduler = 1;

	// Next state will be WAITING, to be set from the next tick (ISR)
	while (ccb->CoreState != WAITING)
		;

	log_debug(coreID, buf, "Master state changed to waiting - core ID=%d\n\r", coreID);

	// Master is now in waiting state, we must wait for *all* cores to
	// be in waiting state also
	sync_ready = 0;
	while (!sync_ready) {
		sync_ready = 1;
		for (int i=1; i<MAX_CPU_CORES; i++) {
			ccbslave = &coreCB[i];
			log_debug(0, buf, "slave %d state=%d\n\r", i, ccbslave->CoreState);
			if (ccbslave->CoreState)
				sync_ready = (sync_ready && ccbslave->CoreState == WAITING);
			else
				log_debug(0, buf, "Slave %d is inactive, state=%d\n\r",
						  i, ccbslave->CoreState);
		}
	}


	// All slaves are also waiting now, we can wait for our state to be
	// set to TIMER_SET. Notify the scheduler that again, we're ready for
	// synchronization
	ccb->SyncScheduler = 1;

	// Next state will be TIMER_SET, to be set by the scheduler.
	while (ccb->CoreState != TIMER_SET)
		;

	log_debug(coreID, buf, "Master state changed to timer_set - core ID=%d\n\r", coreID);

	// Notify the scheduler that again, we're ready for synchronization
	ccb->SyncScheduler = 1;

	// All set, wait for final signal from scheduler
	while (ccb->CoreState != RUNNING)
		;

	log_debug(coreID, buf, "Master finished synchronization - core ID=%d\n\r", coreID);
}

void sync_slave(int offset)
{
	char buf[32];
	int master = 0;
	int coreID = getCoreID();
	struct CoreControlBlock* ccb = &coreCB[coreID];
	struct CoreControlBlock* ccbmaster = &coreCB[master];

	log_debug(coreID, buf, "Slave starting synchronization - core ID=%d\n\r", coreID);

	ccb->CoreState = WAITING;

	// Now wait for the master to pick up all slaves waiting.
	while (ccbmaster->CoreState != TIMER_SET)
		;

	// Master has changed it's state to TIMER_SET
	ccb->CoreState = TIMER_SET;

	log_debug(coreID, buf, "Slave has set timer_set state - core ID=%d\n\r", coreID);

	// Wait for the scheduler to change our status to RUNNING
	ccb->SyncOffset = offset;
	ccb->SyncScheduler = 1;

	while (ccb->CoreState != RUNNING)
		;

	log_debug(coreID, buf, "Slave finished synchronization - core ID=%d\n\r", coreID);
}

void sync_reset()
{
	char buf[32];
	int coreID = getCoreID();
	struct CoreControlBlock* ccb = &coreCB[coreID];

	// Add statements for activating a task again after being put to INACTIVE state
	// place SyncScheduler=1 for the scheduler to move task back to active state

	// State should be running
	if (ccb->CoreState != RUNNING)
		log_debug(coreID, buf, "Sync reset while not running! - core ID=%d\n\r", coreID);

	ccb->CoreState = ACTIVE;
}

RegType_t getOSTickCounter()
{
	struct CoreControlBlock* ccb = &coreCB[getCoreID()];
	return ccb->OSTickCounter;
}

void print_uart(unsigned int corenum, char *buf, const char *fmt, ...)
{
	va_list args;
	va_start(args, fmt);
	vsprintf(buf, fmt, args);

#ifdef MMU_ENABLE
	/* Code to make the printing to the UART reentrant: use the semaphore */
	xSemaphoreTake(screenSem);
#else
	/*
	 * Code to make the printing to the UART reentrant: we'll make a lock
	 * according to a variation of Peterson's algorithm: the Filter algorithm.
	 * This makes sure that the actual printing is done within a critical section.
	 */
	int k;
	bool higher_level;
	for (int l=1; l<NR_OF_CORES; l++) {
		level[corenum] = l;
		last_to_enter[l] = corenum;
		higher_level = true;
		while ((last_to_enter[l] == corenum) && higher_level) {
			k = 0;
			higher_level = false;
			while (!higher_level && k < NR_OF_CORES) {
				if (k != corenum)
					higher_level = (level[k] >= l);
				k++;
			}
		}
	}
#endif

	/* Critical section */
	pl011_uart_puts(buf);
	/* End of Critical section */

#ifdef MMU_ENABLE
	// release lock
	xSemaphoreGive(screenSem);
#else
	// release lock
	level[corenum] = 0;
#endif

	va_end(args);
}
