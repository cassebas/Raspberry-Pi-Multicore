#ifndef IV_CACHE_H
#define IV_CACHE_H

/**
 * This is for invalidation of the cache, implemented in ASM
 *   See invalidate_cache.S
 */
void __asm_invalidate_dcache_all(void);
void __asm_flush_dcache_all(void);

void __asm_invalidate_dcache_range(uint64_t start, uint64_t end);
void __asm_flush_dcache_range(uint64_t start, uint64_t end);

void __asm_invalidate_icache_all(void);

#endif /* ~IV_CACHE_H */
