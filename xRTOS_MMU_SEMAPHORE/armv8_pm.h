#ifndef ARMV8_PM_H
#define ARMV8_PM_H

#ifdef CIRCLE
#include <circle/types.h>
#endif

#define ARMV8_PMCR_MASK         0x3f
#define ARMV8_PMCR_E            (1 << 0) /* Enable all counters */
#define ARMV8_PMCR_P            (1 << 1) /* Event counter reset */
#define ARMV8_PMCR_C            (1 << 2) /* Cycle counter reset */
#define ARMV8_PMCR_D            (1 << 3) /* CCNT counts every 64th cpu cycle */
#define ARMV8_PMCR_X            (1 << 4) /* Export to ETM */
#define ARMV8_PMCR_DP           (1 << 5) /* Disable CCNT if non-invasive debug*/
#define ARMV8_PMCR_LC           (1 << 6) /* Cycle Counter 64bit overflow*/
#define ARMV8_PMCR_N_SHIFT      11       /* Number of counters supported */
#define ARMV8_PMCR_N_MASK       0x1f

#define ARMV8_PMUSERENR_EN_EL0  (1 << 0) /* EL0 access enable */
#define ARMV8_PMUSERENR_CR      (1 << 2) /* Cycle counter read enable */
#define ARMV8_PMUSERENR_ER      (1 << 3) /* Event counter read enable */

#define ARMV8_PMCNTENSET_C      (1<<31) /**< Enable cycle counter */
#define ARMV8_PMCNTENCLR_C      (1<<31) /**< Disable cycle counter */

#define ARMV8_PMCCFILTR_EL0     (1<<27) /* Count cycles in EL2 */

#define ARMV8_PMCEID0_L2DCWB    (1<<24) /* L2 Data cache Write-back event implemented */
#define ARMV8_PMCEID0_L2DCRF    (1<<23) /* L2 Data cache refill event implemented */
#define ARMV8_PMCEID0_L2DC      (1<<22) /* L2 Data cache access event implemented */
#define ARMV8_PMCEID0_L1DCWB    (1<<21) /* L1 Data cache Write-back event implemented */
#define ARMV8_PMCEID0_L1DC      (1<<4)  /* L1 Data cache access event event implemented */
#define ARMV8_PMCEID0_L1DCRF    (1<<3)  /* L1 Data cache refill event implemented */

/* Event types and their number to use in the configuration */
#define PMU_L1D_CACHE_REFILL 0x03  /* 0: L1 Data cache refill */
#define PMU_L1D_CACHE        0x04  /* 1: L1 Data cache access */
#define PMU_L1I_TLB_REFILL   0x02  /* 2: L1 Instruction TLB refill. */
#define PMU_L1D_TLB_REFILL   0x05  /* 3: L1 Data TLB refill. */
#define PMU_MEM_ACCESS       0x13  /* 4: Data memory access */
#define PMU_L1D_CACHE_WB     0x15  /* 5: L1 Data cache Write-back */
#define PMU_L2D_CACHE        0x16  /* 6: L2 Data cache access */
#define PMU_L2D_CACHE_REFILL 0x17  /* 7: L2 Data cache refill */
#define PMU_L2D_CACHE_WB     0x18  /* 8: L2 Data cache Write-back */
#define PMU_BUS_ACCESS       0x19  /* 9: Bus access */


/**
 * Global enable of PMU
 */
inline void enable_pmu()
{
	u64 val=0;
	asm volatile("mrs %[val], pmcr_el0" : [val]"=r" (val));
	asm volatile("msr pmcr_el0, %[val]" : : [val]"r" (val|ARMV8_PMCR_E));
}

inline void enable_cycle_counter()
{
	asm volatile("msr pmcntenset_el0, %0" : : "r" (ARMV8_PMCNTENSET_C));
}

inline void disable_cycle_counter()
{
	asm volatile("msr pmcntenclr_el0, %0" : : "r" (ARMV8_PMCNTENCLR_C));
}

inline u64 read_cycle_counter()
{
	u64 val = 0;
	asm volatile("mrs %0, pmccntr_el0" : "=r" (val));
	return val;
}

/**
 * Reset the cycle counter PMCCNTR_EL0 to zero.
 */
inline void reset_cycle_counter()
{
	u64 val=0;
	asm volatile("mrs %[val], pmcr_el0" : [val]"=r" (val));
	asm volatile("msr pmcr_el0, %[val]" : : [val]"r" (val|ARMV8_PMCR_C));
}


inline u64 read_nr_eventcounters()
{
	/* Read the number of event counters, bits [15:11] in PMCR_EL0 */
	u64 val = 0;
	asm volatile("mrs %0, pmcr_el0" : "=r" (val));
	return ((val >> ARMV8_PMCR_N_SHIFT) & 0x1F);
}

inline u64 read_cei_reg()
{
	/* Read the common event identification register */
	u64 val = 0;
	asm volatile("mrs %0, pmceid0_el0" : "=r" (val));
	return val;
}

inline void config_event_counter(unsigned int counter, unsigned int event)
{
	// select the performance counter, bits [4:0] of PMSELR_EL0
	u64 cntr = ((u64) counter & 0x1F);
	asm volatile("msr pmselr_el0, %[val]" : : [val]"r" (cntr));
	// synchronize context
	asm volatile("isb");
	// write the event type to the PMXEVTYPER
	asm volatile("msr pmxevtyper_el0, %[val]" : : [val]"r" (event & 0xFFFFFFFF));
}

inline void enable_event_counter(unsigned int counter)
{
	u64 counter_bit=0;
	asm volatile(
		"mov x1, #0x1\n\t"
		"lsl %[res], x1, %[val]"
		: [res]"=r" (counter_bit)
		: [val]"r" (counter));
	asm volatile("msr pmcntenset_el0, %[val]" : : [val]"r" (counter_bit));
}

inline void disable_event_counter(unsigned int counter)
{
	u64 counter_bit=0;
	asm volatile(
		"mov x1, #0x1\n\t"
		"lsl %[res], x1, %[val]"
		: [res]"=r" (counter_bit)
		: [val]"r" (counter));
	asm volatile("msr pmcntenclr_el0, %[val]" : : [val]"r" (counter_bit));
}

inline unsigned int read_event_counter(unsigned int counter)
{
	// select the performance counter, bits [4:0] of PMSELR_EL0
	u64 cntr = ((u64) counter & 0x1F);
	asm volatile("msr pmselr_el0, %[val]" : : [val]"r" (cntr));
	// synchronize context
	asm volatile("isb");
	// read the counter
	unsigned int events = 0;
	asm volatile("mrs %[res], pmxevcntr_el0" : [res]"=r" (events));
	return events;
}

/**
 * Reset all event counters to zero (not including PMCCNTR_EL0).
 */
inline void reset_event_counters()
{
	u64 val=0;
	asm volatile("mrs %[val], pmcr_el0" : [val]"=r" (val));
	asm volatile("msr pmcr_el0, %[val]" : : [val]"r" (val|ARMV8_PMCR_P));
}

#endif /* ARMV8_PM_H */
