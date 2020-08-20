/* Taken from Mälardalen benchmark website:
     http://www.mrtc.mdh.se/projects/wcet/benchmarks.html

Slightly modified for our use case.
*/
#include "xRTOS.h"

/*
 * bsort100: Malardalen's Bubblesort definitions.
 */
#define WORSTCASE 1
#define FALSE 0
#define TRUE 1
#define NUMELEMS BSORT_INPUTSIZE
#define MAXDIM   (NUMELEMS+1)

void bsort100_Initialize(volatile int Array[]);
void bsort100_BubbleSort(volatile int Array[]);


/*
 * ns: Malardalen's test of deeply nested loops and non-local exits.
 */
#define NS_NUMELEMS NS_INPUTSIZE
#define NS_DIM 4

void ns_Initialize(int* keys[NS_DIM][NS_DIM][NS_DIM],
				   int* answer[NS_DIM][NS_DIM][NS_DIM]);
int foo(int* keys[NS_DIM][NS_DIM][NS_DIM],
		int* answer[NS_DIM][NS_DIM][NS_DIM],
		int x);
void ns_foo(int* keys[NS_DIM][NS_DIM][NS_DIM],
			int* answer[NS_DIM][NS_DIM][NS_DIM]);


/*
 * matmult: Malardalen's Matrix multiplication of two matrices.
 */
#define UPPERLIMIT MATMULT_INPUTSIZE
typedef int matrix [UPPERLIMIT][UPPERLIMIT];

void matmult_Multiply(matrix A, matrix B, matrix Res);
void matmult_InitSeed(void);
void matmult_Initialize(matrix Array);
int matmult_RandomInteger(void);


/*
 * fir: Malardalen's Finite Input Response implementation.
 */
#define FIR_NUMELEMS FIR_INPUTSIZE
#define FIR_COEFFSIZE 36
#define FIR_SCALE 285

void fir_Initialize(long* in_data);
void fir_fir_filter_int(long* in, long* out, long in_len,
						long* coef, long coef_len,
						long scale);
