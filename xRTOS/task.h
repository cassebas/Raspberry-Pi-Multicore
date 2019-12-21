#ifndef INC_TASK_H
#define INC_TASK_H

#include <stdint.h>
#include <string.h>
#include "rpi-smartstart.h"

#ifdef __cplusplus
extern "C" {
#endif


/**
 * States in which the cores can be for the synchronization mechanism
 * to work.
 */
#define INACTIVE  0
#define ACTIVE    1
#define WAITING   2
#define TIMER_SET 3
#define RUNNING   4


#define SILENT_LEVEL  0
#define ERROR_LEVEL   1
#define WARNING_LEVEL 2
#define INFO_LEVEL    3
#define DEBUG_LEVEL   4

#define LOG_LEVEL INFO_LEVEL

#if LOG_LEVEL >= DEBUG_LEVEL
#define log_debug(corenum, buf, fmt, ...)                \
    do { print_uart(corenum, buf, "DEBUG: %s(): " fmt,   \
                    __func__, __VA_ARGS__); } while (0)
#else
#define log_debug(corenum, buf, fmt, ...)
#endif

#if LOG_LEVEL >= INFO_LEVEL
#define log_info(corenum, buf, fmt, ...)                 \
    do { print_uart(corenum, buf, "INFO: %s(): " fmt,    \
                    __func__, __VA_ARGS__); } while (0)
#else
#define log_info(corenum, buf, fmt, ...)
#endif

#if LOG_LEVEL >= WARNING_LEVEL
#define log_warning(corenum, buf, fmt, ...)              \
    do { print_uart(corenum, buf, "WARNING: %s(): " fmt, \
                    __func__, __VA_ARGS__); } while (0)
#else
#define log_warning(corenum, buf, fmt, ...)
#endif

#if LOG_LEVEL >= ERROR_LEVEL
#define log_error(corenum, buf, fmt, ...)                \
    do { print_uart(corenum, buf, "ERROR: %s(): " fmt,   \
                    __func__, __VA_ARGS__); } while (0)
#else
#define log_error(corenum, buf, fmt, ...)
#endif

#define OFFSET_FACTOR 1

/*--------------------------------------------------------------------------}
{							TASK HANDLE DEFINED								}
{--------------------------------------------------------------------------*/
struct TaskControlBlock;
typedef struct TaskControlBlock* TaskHandle_t;

/***************************************************************************}
{					    PUBLIC INTERFACE ROUTINES						    }
****************************************************************************/

/*-[ xRTOS_Init ]-----------------------------------------------------------}
.  Initializes xRTOS system and must be called before any other xRTOS call
.--------------------------------------------------------------------------*/
void xRTOS_Init (void);


/*-[ xTaskCreate ]----------------------------------------------------------}
.  Creates an xRTOS task on the given core.
.--------------------------------------------------------------------------*/
void xTaskCreate (uint8_t corenum,									// The core number to run task on
				  void (*pxTaskCode) (void* pxParam),				// The code for the task
				  const char* const pcName,							// The character string name for the task
				  const unsigned int usStackDepth,					// The stack depth in register size for the task stack 
				  void* const pvParameters,							// Private parameter that may be used by the task
				  uint8_t uxPriority,								// Priority of the task
				  TaskHandle_t* const pxCreatedTask);				// A pointer to return the task handle (NULL if not required)


/*-[ xTaskDelay ]-----------------------------------------------------------}
.  Moves an xRTOS task from the ready task list into the delayed task list
.  until the time wait in timer ticks is expired. This effectively stalls 
.  any task processing at that time for the fixed period of time. 
.--------------------------------------------------------------------------*/
void xTaskDelay (const unsigned int time_wait);


/*-[ xTaskStartScheduler ]--------------------------------------------------}
.  starts the xRTOS task scheduler effectively starting the whole system
.--------------------------------------------------------------------------*/
void xTaskStartScheduler (void);

/*-[ xTaskGetNumberOfTasks ]------------------------------------------------}
.  Returns the number of xRTOS tasks assigned to the core this is called
.--------------------------------------------------------------------------*/
unsigned int xTaskGetNumberOfTasks (void);

/*-[ xLoadPercentCPU ]------------------------------------------------------}
.  Returns the load on the core this is called from in percent (0 - 100)
.--------------------------------------------------------------------------*/
unsigned int xLoadPercentCPU(void);

void sync_master(void);
void sync_slave(int offset);
void sync_reset(void);

RegType_t getOSTickCounter(void);

void print_uart(unsigned int corenum, char *buf, const char *fmt, ...);

#ifdef __cplusplus
}
#endif
#endif /* INC_TASK_H */



