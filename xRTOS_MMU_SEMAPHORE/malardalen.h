/* Taken from Mälardalen benchmark website:
     http://www.mrtc.mdh.se/projects/wcet/benchmarks.html

Slightly modified for our use case.
*/
#ifndef MALARDALEN_H
#define MALARDALEN_H

#include "corunners_definition.h"
#ifdef CIRCLE
#include "randomwrapper.h"
#endif

#ifndef CIRCLE
#include "types.h"
#endif

/*
 * bsort100: Malardalen's Bubblesort definitions.
 */
#define WORSTCASE 1
#define NUMELEMS MALARDALEN_BSORT_INPUTSIZE
#define MAXDIM   (NUMELEMS+1)

#ifdef CIRCLE
void bsort100_Initialize(volatile int Array[], RandomWrapper*);
#else
void bsort100_Initialize(volatile int Array[]);
#endif
void bsort100_BubbleSort(volatile int Array[]);


/*
 * ns: Malardalen's test of deeply nested loops and non-local exits.
 */
#define NS_ELEMS MALARDALEN_NS_INPUTSIZE

void ns_Initialize(int (*keys)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
				   int (*answer)[NS_ELEMS][NS_ELEMS][NS_ELEMS]);
int foo(int (*keys)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
		int (*answer)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
		int x);
void ns_foo(int (*keys)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
			int (*answer)[NS_ELEMS][NS_ELEMS][NS_ELEMS]);


/*
 * matmult: Malardalen's Matrix multiplication of two matrices.
 */
#define UPPERLIMIT MALARDALEN_MATMULT_INPUTSIZE
typedef int matrix [UPPERLIMIT][UPPERLIMIT];

void matmult_Multiply(matrix A, matrix B, matrix Res);
void matmult_InitSeed(void);
void matmult_Initialize(matrix Array);
int matmult_RandomInteger(void);


/*
 * fir: Malardalen's Finite Input Response implementation.
 */
#define FIR_NUMELEMS MALARDALEN_FIR_INPUTSIZE
#define FIR_COEFFSIZE 36
#define FIR_SCALE 285

void fir_Initialize(long* in_data);
void fir_filter_int(long* in, long* out, long in_len,
					long* coef, long coef_len,
					long scale);

#endif /* MALARDALEN_H */
