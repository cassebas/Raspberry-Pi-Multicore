/*
 * synthetic_bench.h
 *
 *  Created on: Nov 11, 2019
 *      Author: Caspar Treijtel
 */

#ifndef SYNTHETIC_BENCH_H
#define SYNTHETIC_BENCH_H

#define SYNBENCH_DATASIZE 250

/**
Synthetic benchmark inspired by the paper `Predictable and Efficient Virtual Addressing for
 Safety-Critical Real-Time Systems', written by Bennet and Audsley (2001).
 */

/**
 * Type bigstruct_t is (with int being 4 bytes) a 2K struct.
 */
typedef struct bigstruct {
	int id;
	int data[511];
} bigstruct_t;


/* bigstruct_t* create_array(void); */
/* void delete_array(bigstruct_t* data); */

void array_access_linear(volatile bigstruct_t* data);
void array_access_random(volatile bigstruct_t* data);
void array_access_alternate(volatile bigstruct_t* data);

#endif /* SYNTHETIC_BENCH_H */
