#ifndef ARMV8_PM_H
#define ARMV8_PM_H

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
#define PMU_BR_MIS_PRED      0x10  /* 2: Mis-/not predicted branch speculatively exec. */
#define PMU_BR_PRED          0x12  /* 3: Predictable branch speculatively executed */
#define PMU_MEM_ACCESS       0x13  /* 4: Data memory access */
#define PMU_L1D_CACHE_WB     0x15  /* 5: L1 Data cache Write-back */
#define PMU_L2D_CACHE        0x16  /* 6: L2 Data cache access */
#define PMU_L2D_CACHE_REFILL 0x17  /* 7: L2 Data cache refill */
#define PMU_L2D_CACHE_WB     0x18  /* 8: L2 Data cache Write-back */
#define PMU_BUS_ACCESS       0x19  /* 9: Bus access */

#endif /* ARMV8_PM_H */
