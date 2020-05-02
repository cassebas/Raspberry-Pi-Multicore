/* Taken from Mälardalen benchmark website:
     http://www.mrtc.mdh.se/projects/wcet/benchmarks.html

Slightly modified for our use case.
*/

/*
 * bsort100: Malardalen's Bubblesort definitions.
 */
#define WORSTCASE 1
#define FALSE 0
#define TRUE 1
#define NUMELEMS 10000
#define MAXDIM   (NUMELEMS+1)

void bsort100_Initialize(int Array[]);
void bsort100_BubbleSort(int Array[]);


/*
 * edn: Malardalen's Finite Impulse Response (FIR) filter calculations.
 */
#define N 100
#define ORDER 50

void vec_mpy1(short y[], const short x[], short scaler);
long int mac(const short *a, const short *b, long int sqr, long int *sum);
void fir(const short array1[], const short coeff[], long int output[]);
void fir_no_red_ld(const short x[], const short h[], long int y[]);
long int latsynth(short b[], const short k[], long int n, long int f);
void iir1(const short *coefs, const short *input, long int *optr, long int *state);
long int codebook(long int mask, long int bitchanged, long int numbasis, long int codeword, long int g, const short *d, short ddim, short theta);
void jpegdct(short *d, short *r);

void edn_Calculate(void);
