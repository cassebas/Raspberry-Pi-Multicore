/**
 * Provide _sbrk to be able to use malloc from newlib,
 * source of the following code:
 *   https://embdev.net/topic/linker-error-undefined-reference-to-_sbrk
 *
 * Warning: check for enough heap space is not implemented, so using
 * malloc, it is the user's responsibility to not allocate too much.
 */

/* for caddr_t (typedef char * caddr_t;) */
#include <sys/types.h>

extern int __HEAP_START;

caddr_t _sbrk(int incr)
{
	static unsigned char *heap = NULL;
	unsigned char *prev_heap;

	if (heap == NULL) {
		heap = (unsigned char *)&__HEAP_START;
	}
	prev_heap = heap;
	heap += incr;
	return (caddr_t) prev_heap;
}
