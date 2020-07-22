/* Taken from Mälardalen benchmark website:
     http://www.mrtc.mdh.se/projects/wcet/benchmarks.html
*/

#include "malardalen.h"
#include <stdlib.h>

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
void bsort100_Initialize(int Array[])
{
	int  Index, fact;
	static int seed;

#ifdef WORSTCASE
	factor = -1;
#else
	factor = 1;
#endif

	srand(++seed);

	fact = factor;
	for (Index = 1; Index <= NUMELEMS; Index ++) {
		Array[Index] = rand() * fact/* * KNOWN_VALUE*/;
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


/*
 * edn: Malardalen's Finite Impulse Response (FIR) filter calculations.
 */

/************************************************************************
*	Simple vector multiply				*
************************************************************************/
void
vec_mpy1(short y[], const short x[], short scaler)
{
	long int        i;

	for (i = 0; i < 150; i++)
		y[i] += ((scaler * x[i]) >> 15);
}


/*****************************************************
*			Dot Product	      *
*****************************************************/
long int
mac(const short *a, const short *b, long int sqr, long int *sum)
{
	long int        i;
	long int        dotp = *sum;

	for (i = 0; i < 150; i++) {
		dotp += b[i] * a[i];
		sqr += b[i] * b[i];
	}

	*sum = dotp;
	return sqr;
}


/*****************************************************
*		FIR Filter		     *
*****************************************************/
void
fir(const short array1[], const short coeff[], long int output[])
{
	long int        i, j, sum;

	for (i = 0; i < N - ORDER; i++) {
		sum = 0;
		for (j = 0; j < ORDER; j++) {
			sum += array1[i + j] * coeff[j];
		}
		output[i] = sum >> 15;
	}
}

/****************************************************
*	FIR Filter with Redundant Load Elimination
						
By doing two outer loops simultaneously, you can potentially  reuse data (depending on the DSP architecture).
x and h  only  need to be loaded once, therefore reducing redundant loads.
This reduces memory bandwidth and power.
*****************************************************/
void
fir_no_red_ld(const short x[], const short h[], long int y[])
{
	long int        i, j;
	long int        sum0, sum1;
	short           x0, x1, h0, h1;
	for (j = 0; j < 100; j += 2) {
		sum0 = 0;
		sum1 = 0;
		x0 = x[j];
		for (i = 0; i < 32; i += 2) {
			x1 = x[j + i + 1];
			h0 = h[i];
			sum0 += x0 * h0;
			sum1 += x1 * h0;
			x0 = x[j + i + 2];
			h1 = h[i + 1];
			sum0 += x1 * h1;
			sum1 += x0 * h1;
		}
		y[j] = sum0 >> 15;
		y[j + 1] = sum1 >> 15;
	}
}

/*******************************************************
*	Lattice Synthesis	           *
* This function doesn't follow the typical DSP multiply two  vector operation, but it will point out the compiler's flexibility   ********************************************************/
long int
latsynth(short b[], const short k[], long int n, long int f)
{
	long int        i;

	f -= b[n - 1] * k[n - 1];
	for (i = n - 2; i >= 0; i--) {
		f -= b[i] * k[i];
		b[i + 1] = b[i] + ((k[i] * (f >> 16)) >> 16);
	}
	b[0] = f >> 16;
	return f;
}

/*****************************************************
*			IIR Filter		     *
*****************************************************/
void
iir1(const short *coefs, const short *input, long int *optr, long int *state)
{
	long int        x;
	long int        t;
	long int        n;

	x = input[0];
	for (n = 0; n < 50; n++) {
		t = x + ((coefs[2] * state[0] + coefs[3] * state[1]) >> 15);
		x = t + ((coefs[0] * state[0] + coefs[1] * state[1]) >> 15);
		state[1] = state[0];
		state[0] = t;
		coefs += 4;	/* point to next filter coefs  */
		state += 2;	/* point to next filter states */
	}
	*optr++ = x;
}

/*****************************************************
*	Vocoder Codebook Search 	     *
*****************************************************/
long int
codebook(long int mask, long int bitchanged, long int numbasis, long int codeword, long int g, const short *d, short ddim, short theta)
/*
 * dfm (mask=d  bitchanged=1 numbasis=17  codeword=e[0] , g=d, d=a, ddim=c,
 * theta =1
 */

{
	long int        j;
	long int        tmpMask;

	tmpMask = mask << 1;
	for (j = bitchanged + 1; j <= numbasis; j++) {



/*		
 * The following code is removed since it gave a memory access exception.
 * It is OK since the return value does not control the flow.
 * The loop always iterates a fixed number of times independent of the loop body.
 
    if (theta == !(!(codeword & tmpMask)))
			g += *(d + bitchanged * ddim + j);
		else
			g -= *(d + bitchanged * ddim + j);
		tmpMask <<= 1;
*/
	}
	return g;
}


/*****************************************************
*		JPEG Discrete Cosine Transform 		     *
*****************************************************/
void
jpegdct(short *d, short *r)
{
	long int        t[12];
	short           i, j, k, m, n, p;
	for (k = 1, m = 0, n = 13, p = 8; k <= 8; k += 7, m += 3, n += 3, p -= 7, d -= 64) {
		for (i = 0; i < 8; i++, d += p) {
			for (j = 0; j < 4; j++) {
				t[j] = d[k * j] + d[k * (7 - j)];
				t[7 - j] = d[k * j] - d[k * (7 - j)];
			}
			t[8] = t[0] + t[3];
			t[9] = t[0] - t[3];
			t[10] = t[1] + t[2];
			t[11] = t[1] - t[2];
			d[0] = (t[8] + t[10]) >> m;
			d[4 * k] = (t[8] - t[10]) >> m;
			t[8] = (short) (t[11] + t[9]) * r[10];
			d[2 * k] = t[8] + (short) ((t[9] * r[9]) >> n);
			d[6 * k] = t[8] + (short) ((t[11] * r[11]) >> n);
			t[0] = (short) (t[4] + t[7]) * r[2];
			t[1] = (short) (t[5] + t[6]) * r[0];
			t[2] = t[4] + t[6];
			t[3] = t[5] + t[7];
			t[8] = (short) (t[2] + t[3]) * r[8];
			t[2] = (short) t[2] * r[1] + t[8];
			t[3] = (short) t[3] * r[3] + t[8];
			d[7 * k] = (short) (t[4] * r[4] + t[0] + t[2]) >> n;
			d[5 * k] = (short) (t[5] * r[6] + t[1] + t[3]) >> n;
			d[3 * k] = (short) (t[6] * r[5] + t[1] + t[2]) >> n;
			d[1 * k] = (short) (t[7] * r[7] + t[0] + t[3]) >> n;
		}
	}
}

void edn_Calculate(void)
{
	short a[200] = {
        0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000,
        0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00,
        0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200,
        0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300,
        0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000,
        0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00,
        0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200,
        0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300,
        0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000,
        0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00,
        0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200,
        0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300,
        0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000,
        0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00,
        0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200,
        0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300,
        0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000,
        0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00,
        0x0800, 0x0200, 0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200,
        0xf800, 0xf300, 0x0400, 0x0000, 0x07ff, 0x0c00, 0x0800, 0x0200, 0xf800, 0xf300,
        0x0400};
	short b[200] = {
        0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60,
        0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20,
        0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600,
        0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200,
        0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60,
        0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20,
        0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600,
        0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200,
        0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60,
        0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20,
        0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600,
        0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200,
        0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60,
        0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20,
        0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600,
        0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200,
        0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60,
        0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20,
        0x0c00, 0xf600, 0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600,
        0xf400, 0xf200, 0xf000, 0x0c60, 0x0c40, 0x0c20, 0x0c00, 0xf600, 0xf400, 0xf200,
        0xf000};

	short c = 0x3;
	long int output[200];
	long int d = 0xAAAA;
	int e[1] = {0xEEEE};

	vec_mpy1(a, b, c);
	c = mac(a, b, (long int) c, (long int *) output);
	fir(a, b, output);
	fir_no_red_ld(a, b, output);
	d = latsynth(a, b, N, d);
	iir1(a, b, &output[100], output);
	e[0] = codebook(d, 1, 17, e[0], d, a, c, 1);
	jpegdct(a, b);
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
