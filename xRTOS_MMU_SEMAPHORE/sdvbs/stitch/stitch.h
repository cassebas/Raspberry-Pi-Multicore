/********************************
Author: Sravanthi Kota Venkata
********************************/

#ifndef _SCRIPT_STITCH_
#define _SCRIPT_STITCH_

#include "../common/sdvbs_common.h"

/* Added by CT, convenience method: */
/* easier calling of benchmark in 1 statement */
void stitch_wrapper(I2D* Icur);

F2D* dist2(I2D* x, F2D* c);
F2D* extractFeatures(I2D* I, F2D* x, F2D* y);
F2D* getANMS (F2D *points, int r);
F2D* harris(I2D* im);
I2D* matchFeatures(F2D* vecF1, F2D* vecF2);
F2D* maxWindow(F2D* im, I2D* window);
F2D* supress(F2D* im, F2D* im1);
int script_stitch();

#endif



