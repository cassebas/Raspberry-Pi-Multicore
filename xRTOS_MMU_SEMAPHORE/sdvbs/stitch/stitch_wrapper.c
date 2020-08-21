#include "stitch.h"

void stitch_wrapper(I2D* Icur)
{
	F2D *x, *y, *v, *interestPnts, *Fcur, *int1, *int2;
	int i, j;
	unsigned int* start, *endC, *elapsed;

	v = harris(Icur);
	interestPnts = getANMS(v, 24);

	int1 = fMallocHandle(interestPnts->height, 1);
	int2 = fSetArray(interestPnts->height, 1, 0);

	for(i=0; i<int1->height; i++)
	{
		asubsref(int1,i) = subsref(interestPnts,i,0);
		asubsref(int2,i) = subsref(interestPnts,i,1);
	}

	Fcur = extractFeatures(Icur, int1, int2);  
}
