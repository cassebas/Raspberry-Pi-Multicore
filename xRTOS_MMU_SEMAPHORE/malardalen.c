/* Taken from Mälardalen benchmark website:
     http://www.mrtc.mdh.se/projects/wcet/benchmarks.html
*/

#include "malardalen.h"
#ifndef CIRCLE
#include <stdlib.h>
#endif

/*
 * bsort100: Malardalen's Bubblesort definitions.
 */

/* All output disabled for wcsim */
#define WCSIM 1

int Array[MAXDIM], Seed;
int factor;

/*
 * Initializes given array with randomly generated integers.
 */
#ifndef CIRCLE
void bsort100_Initialize(volatile int Array[])
#else
void bsort100_Initialize(volatile int Array[], RandomWrapper* rand)
#endif
{
	int  Index, fact;
#ifndef CIRCLE
	static int seed;
#endif

#ifdef WORSTCASE
	factor = -1;
#else
	factor = 1;
#endif

#ifndef CIRCLE
	srand(++seed);
#endif

	fact = factor;
	for (Index = 1; Index <= NUMELEMS; Index ++) {
#ifndef CIRCLE
		Array[Index] = rand() * fact/* * KNOWN_VALUE*/;
#else
		Array[Index] = get_number(rand) * fact/* * KNOWN_VALUE*/;
#endif
	}
}


/*
 * Sorts an array of integers of size NUMELEMS in ascending order.
 */
void bsort100_BubbleSort(volatile int Array[])
{
	int Sorted = FALSE;
	int Temp, Index, i;

	for (i = 1;
	     i <= NUMELEMS - 1;	/* apsim_loop 1 0 */
	     i++) {
		Sorted = TRUE;
		for (Index = 1;
		     Index <= NUMELEMS - 1;	/* apsim_loop 10 1 */
		     Index++) {
			if (Index > NUMELEMS - i)
				break;
			if (Array[Index] > Array[Index + 1]) {
				Temp = Array[Index];
				Array[Index] = Array[Index + 1];
				Array[Index + 1] = Temp;
				Sorted = FALSE;
			}
		}

		if (Sorted)
			break;
	}

#ifndef WCSIM
	if (Sorted || i == 1)
		fprintf(stderr, "array was successfully sorted in %d passes\n", i - 1);
	else
		fprintf(stderr, "array was unsuccessfully sorted in %d passes\n", i - 1);
#endif
}


/*
 * ns: Malardalen's test of deeply nested loops and non-local exits.
 */
void ns_Initialize(int (*keys)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
				   int (*answer)[NS_ELEMS][NS_ELEMS][NS_ELEMS])
{
	// CT: own code to fill the keys and answer arrays with the same
	//     numbers as in the benchmark code, but more/less numbers
	//     depending on the number of elements as defined.

	// The nr of dimensions is always 4
	int i,j,k,l;
	for (i=0; i<NS_ELEMS; i++)
		for (j=0; j<NS_ELEMS; j++)
			for (k=0; k<NS_ELEMS; k++)
				for (l=0; l<NS_ELEMS; l++) {
					keys[i][j][k][l] = i;
					answer[i][j][k][l] = i*111 + 123;
				}

	i = NS_ELEMS - 1;
#ifdef FIND_TARGET
	keys[i][i][i][i] = 400;
#else
	keys[i][i][i][i] = 400;	/* not searched for */
#endif
}

int foo(int (*keys)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
		int (*answer)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
		int x)
{
  int i,j,k,l;

  for(i=0; i<NS_ELEMS; i++)
    for(j=0 ; j<NS_ELEMS ; j++)
      for(k=0 ; k<NS_ELEMS ; k++)
        for(l=0 ; l<NS_ELEMS ; l++)
        {
          if( keys[i][j][k][l] == x )
            {
              return answer[i][j][k][l] + keys[i][j][k][l];
            }
        }
  return -1;
}

void ns_foo(int (*keys)[NS_ELEMS][NS_ELEMS][NS_ELEMS],
			int (*answer)[NS_ELEMS][NS_ELEMS][NS_ELEMS])
{
	foo(keys, answer, 400);
}



/*
 * matmult: Malardalen's Matrix multiplication of two matrices.
 */

void matmult_InitSeed(void)
/*
 * Initializes the seed used in the random number generator.
 */
{
  /* ***UPPSALA WCET***:
     changed Thomas Ls code to something simpler.
   Seed = KNOWN_VALUE - 1; */
  Seed = 0;
}

void matmult_Initialize(matrix Array)
/*
 * Intializes the given array with random integers.
 */
{
   int OuterIndex, InnerIndex;

   for (OuterIndex = 0; OuterIndex < UPPERLIMIT; OuterIndex++)
      for (InnerIndex = 0; InnerIndex < UPPERLIMIT; InnerIndex++)
         Array[OuterIndex][InnerIndex] = matmult_RandomInteger();
}

int matmult_RandomInteger(void)
/*
 * Generates random integers between 0 and 8095
 */
{
   Seed = ((Seed * 133) + 81) % 8095;
   return (Seed);
}

void matmult_Multiply(matrix A, matrix B, matrix Res)
/*
 * Multiplies arrays A and B and stores the result in ResultArray.
 */
{
   register int Outer, Inner, Index;

   for (Outer = 0; Outer < UPPERLIMIT; Outer++)
      for (Inner = 0; Inner < UPPERLIMIT; Inner++)
      {
         Res [Outer][Inner] = 0;
         for (Index = 0; Index < UPPERLIMIT; Index++)
            Res[Outer][Inner]  +=
               A[Outer][Index] * B[Index][Inner];
       }
}


/*
 * Initializes given array with randomly generated integers.
 */
void fir_Initialize(long* in_data)
{
	int  Index, fact;
	static int seed;

	srand(++seed);

	fact = factor;
	for (int i=0; i<FIR_NUMELEMS; i++) {
		in_data[i] = rand();
	}
}

void fir_filter_int(long* in,long* out,long in_len,
                    long* coef,long coef_len,
                    long scale)
{
	long i,j,coef_len2,acc_length;
	long acc;
	long *in_ptr,*data_ptr,*coef_start,*coef_ptr,*in_end;

	/* set up for coefficients */
	coef_start = coef;
	coef_len2 = (coef_len + 1) >> 1;

	/* set up input data pointers */
	in_end = in + in_len - 1;
	in_ptr = in + coef_len2 - 1;

	/* initial value of accumulation length for startup */
	acc_length = coef_len2;

	for(i = 0 ; i < in_len ; i++) {

		/* set up pointer for accumulation */
		data_ptr = in_ptr;
		coef_ptr = coef_start;

		/* do accumulation and write result with scale factor */

		acc = (long)(*coef_ptr++) * (*data_ptr--);
		for(j = 1 ; j < acc_length ; j++)
			acc += (long)(*coef_ptr++) * (*data_ptr--);
		*out++ = (int)(acc/scale);

		/* check for end case */

		if(in_ptr == in_end) {
			acc_length--;       /* one shorter each time */
			coef_start++;       /* next coefficient each time */
		}

		/* if not at end, then check for startup, add to input pointer */

		else {
			if(acc_length < coef_len) acc_length++;
			in_ptr++;
		}
	}
}
