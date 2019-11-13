/*
 * synthetic_bench.c
 *
 *  Created on: Nov 11, 2019
 *      Author: Caspar Treijtel
 
*/

#include <stdlib.h>
#include "synthetic_bench.h"

/* bigstruct_t* create_array() */
/* { */
/* 	bigstruct_t *big_array = (bigstruct_t *) calloc(SYNBENCH_DATASIZE, sizeof(bigstruct_t)); */
/* 	if (big_array != NULL) { */
/* 		return big_array; */
/* 	} else { */
/* 		return NULL; */
/* 	} */
/* } */

/* void delete_array(bigstruct_t* data) */
/* { */
/* 	if (data != NULL) { */
/* 		free(data); */
/* 	} */
/* } */

void array_access_linear(volatile bigstruct_t* data)
{
	if (data != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[i].id;
		}
	}
}

void array_access_random(volatile bigstruct_t* data)
{
	/* TODO: make array access random! */
	if (data != NULL) {
		for (int i=0; i<SYNBENCH_DATASIZE; ++i) {
			data[i].id;
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
