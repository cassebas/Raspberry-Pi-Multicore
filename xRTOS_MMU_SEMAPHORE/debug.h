#ifndef DEBUG_H
#define DEBUG_H

#include "xRTOS.h"

#define SILENT_LEVEL  0
#define ERROR_LEVEL   1
#define WARNING_LEVEL 2
#define INFO_LEVEL    3
#define DEBUG_LEVEL   4

#ifdef DEBUG_ENABLE
#define LOG_LEVEL DEBUG_LEVEL
#else
#define LOG_LEVEL INFO_LEVEL
#endif

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

#endif /* DEBUG_H */
