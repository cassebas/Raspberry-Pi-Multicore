/* Taken from Mälardalen benchmark website:
     http://www.mrtc.mdh.se/projects/wcet/benchmarks.html
*/

#include "malardalen.h"

/* All output disabled for wcsim */
#define WCSIM 1

int Array[MAXDIM], Seed;
int factor;

/*
 * Initializes given array with randomly generated integers.
 */
void bsort100_Initialize(int Array[])
{
	int  Index, fact;

#ifdef WORSTCASE
	factor = -1;
#else
	factor = 1;
#endif

	fact = factor;
	for (Index = 1; Index <= NUMELEMS; Index ++) {
		Array[Index] = Index * fact/* * KNOWN_VALUE*/;
	}
}


/*
 * Sorts an array of integers of size NUMELEMS in ascending order.
 */
void bsort100_BubbleSort(int Array[])
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
