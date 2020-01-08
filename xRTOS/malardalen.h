/* Taken from Mälardalen benchmark website:
     http://www.mrtc.mdh.se/projects/wcet/benchmarks.html

Slightly modified for our use case.
*/

#define WORSTCASE 1
#define FALSE 0
#define TRUE 1
#define NUMELEMS 100
#define MAXDIM   (NUMELEMS+1)

void bsort100_Initialize(int Array[]);
void bsort100_BubbleSort(int Array[]);
