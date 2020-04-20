/*
 * synthetic_bench.c
 *
 *  Created on: Nov 11, 2019
 *      Author: Caspar Treijtel
 
*/

#include <stdlib.h>
#include "synthetic_bench.h"

void array_access_linear(volatile bigstruct_t* data)
{
	volatile int sum = 0;
	if (data != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			sum += data[i].id;
		}
	}
}

void array_write_linear(volatile bigstruct_t* data)
{
	if (data != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[i].id = 0xff;
		}
	}
}

void array_access_randomize(volatile int* idx, int corenum)
{
	int seed = corenum + 1;
	srand(seed);
	for (int i=0; i<SYNBENCH_DATASIZE; i++) {
		idx[i] = rand() % SYNBENCH_DATASIZE;
	}
}

void array_access_random(volatile bigstruct_t* data, volatile int* idx)
{
	volatile int sum = 0;
	if (data != NULL && idx != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			sum += data[idx[i]].id;
		}
	}
}

void array_write_random(volatile bigstruct_t* data, volatile int* idx)
{
	if (data != NULL && idx != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[idx[i]].id = 0xff;
		}
	}
}

void array_access_alternate(volatile bigstruct_t* data)
{
	/* TODO: make array access alternate! */
	if (data != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[i].id;
		}
	}
}
