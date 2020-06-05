#ifndef MUTEX_H
#define MUTEX_H

#define NR_OF_LOCKS 2

#define UART_LOCK 0
#define MEM_LOCK 1

void init_lock(int);
void lock(int, int);
void unlock(int, int);

#endif // MUTEX_H
