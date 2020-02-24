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
	if (data != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[i].id;
		}
	}
}

void array_access_randomize(volatile int* idx)
{
	static int seed;

	srand(++seed);
	for (int i=0; i<SYNBENCH_DATASIZE; i++) {
		idx[i] = rand() % SYNBENCH_DATASIZE;
	}
}

void array_access_random(volatile bigstruct_t* data, volatile int* idx)
{
	/* TODO: make array access random! */
	if (data != NULL && idx != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[idx[i]].id;
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
