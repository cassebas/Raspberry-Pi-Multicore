/*
 * synthetic_bench.c
 *
 *  Created on: Nov 11, 2019
 *      Author: Caspar Treijtel
 
*/

#include <stdlib.h>
#include "synthetic_bench.h"

#include "random_sets.h"

void array_access_linear(volatile bigstruct_t* data)
{
	if (data != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[i].id;
		}
	}
}

void array_access_randomize(volatile int* idx, int corenum, int iter)
{
	int mysetidx = (iter * 4 + corenum) % MAX_SETS;
	for (int i=0; i<SYNBENCH_DATASIZE; i++) {
		idx[i] = random_set[mysetidx][i];
	}
}

void array_access_random(volatile bigstruct_t* data, volatile int* idx)
{
	if (data != NULL && idx != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[idx[i]].id;
		}
	}
}

void array_write_random(volatile bigstruct_t* data, volatile int* idx)
{
	static int seed;
	srand(++seed);

	if (data != NULL && idx != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[idx[i]].id = i;
			for (int j=0; j<BIGSTRUCT_DATASIZE; ++j) {
				data[idx[i]].data[j] = rand();
			}
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
