#include "svm.h"

/* Added by CT, convenience method: */
/* easier calling of benchmark in 1 statement */
void svm_wrapper(F2D* trn1, F2D* tst1, F2D* trn2, F2D* tst2,
				 int iter, int N, int Ntst)
{
	int i, j, k, n;
	F2D* Yoffset;
	alphaRet* alpha;
	F2D *a_result, *result;
	F2D *s;
	F2D *b_result;
	F2D *Xtst, *Ytst;
	unsigned int* start, *stop, *elapsed;
	char im1[256];
	int dim = 256;

	alpha = getAlphaFromTrainSet(N, trn1, trn2, iter);
	a_result = alpha->a_result;
	b_result = alpha->b_result;
	Yoffset = fSetArray(iter, N, 0);

	Xtst = usps_read_partial(tst1, tst2, -1, 1, Ntst/iter, iter);
	Ytst = usps_read_partial(tst1, tst2, -1, 0, Ntst/iter, iter);

	for(i=0; i<iter; i++)
	{
		F2D *temp;
		temp = usps_read_partial(trn1, trn2, i, 0, N/iter, iter);
		for(j=0; j<N; j++)
			subsref(Yoffset,i,j) = asubsref(temp,j);
		fFreeHandle(temp);
	}

	result = fSetArray(Ntst,1,0);
	for( n=0; n<Ntst; n++)
	{
		float maxs=0;
		s=fSetArray(iter,1,0);
		for( i=0; i<iter; i++)
		{
			for (j=0; j<N; j++)
			{
				if (subsref(a_result,i,j) > 0)
				{
					F2D *Xtemp, *XtstTemp, *X;
					X = alpha->X;
					Xtemp = fDeepCopyRange(X,j,1,0,X->width);
					XtstTemp = fDeepCopyRange(Xtst, n,1,0,Xtst->width);
					asubsref(s,i) = asubsref(s,i) + subsref(a_result,i,j) * subsref(Yoffset,i,j) * polynomial(3,Xtemp,XtstTemp, dim);
					fFreeHandle(Xtemp); 
					fFreeHandle(XtstTemp); 
				}
			}
			asubsref(s,i) = asubsref(s,i) - asubsref(b_result,i);
			if( asubsref(s,i) > maxs)
				maxs = asubsref(s,i);
		}

		fFreeHandle(s);
		asubsref(result,n) = maxs;
	}
}
