# If cross compiling from windows use native GNU-Make 4.2.1
# https://sourceforge.net/projects/ezwinports/files/
# download "make-4.2.1-without-guile-w32-bin.zip" and set it on the enviroment path
# There is no need to install cygwin or any of that sort of rubbish

ifeq ($(OS), Windows_NT)
	#WINDOWS USE THESE DEFINITIONS
	RM = -del /q
	SLASH = \\
else
	#LINUX USE THESE DEFINITIONS
	RM = -rm -f
	SLASH = /
endif 

TOOLCHAIN_BASE = $(HOME)/local/share
CROSS_COMPILER_ARM = $(TOOLCHAIN_BASE)/gcc-arm-eabi-8.3
CROSS_COMPILER_AARCH64 = $(TOOLCHAIN_BASE)/gcc-aarch64-elf-8.3
RASPBERRY_PI_NETWORKBOOT = $(HOME)/git/Raspberry-Pi-Networkboot
INSTALL_DIR = $(RASPBERRY_PI_NETWORKBOOT)/tftp

RANDOM_SETS_H = random_sets.h

$(RANDOM_SETS_H):
	../experiment/make_random_set_arrays.sh $@

install: Pi3-64
	cp -p DiskImg/kernel8.img $(INSTALL_DIR)
.PHONY: install

Pi3-64: CFLAGS = -Wall -O3 -mcpu=cortex-a53+fp+simd -ffreestanding -nostartfiles -std=gnu11 -mstrict-align -fno-tree-loop-vectorize -fno-tree-slp-vectorize -Wno-nonnull-compare $(SYNBENCH_DATASIZE) $(BENCHMARK_CONFIG) $(DISABLE_CACHE) $(NO_CACHE_MGMT)
Pi3-64: ARMGNU = $(CROSS_COMPILER_AARCH64)/bin/aarch64-elf
Pi3-64: LINKERFILE = rpi64.ld
Pi3-64: SMARTSTART = SmartStart64.S
Pi3-64: IV_CACHE = invalidate_cache.S
Pi3-64: IMGFILE = kernel8.img

Pi3: CFLAGS = -Wall -O3 -mcpu=cortex-a53 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffreestanding -nostartfiles -std=gnu11 -mno-unaligned-access -fno-tree-loop-vectorize -fno-tree-slp-vectorize -Wno-nonnull-compare
Pi3: ARMGNU = $(CROSS_COMPILER_ARM)/bin/arm-eabi
Pi3: LINKERFILE = rpi32.ld
Pi3: SMARTSTART = SmartStart32.S
Pi3: IMGFILE = kernel8-32.img

Pi2: CFLAGS = -Wall -O3 -mcpu=cortex-a7 -mfpu=neon -mfloat-abi=hard -ffreestanding -nostartfiles -std=gnu11 -mno-unaligned-access -fno-tree-loop-vectorize -fno-tree-slp-vectorize -Wno-nonnull-compare
Pi2: ARMGNU = $(CROSS_COMPILER_ARM)/bin/arm-eabi
Pi2: LINKERFILE = rpi32.ld
Pi2: SMARTSTART = SmartStart32.S
Pi2: IMGFILE = kernel7.img

Pi1:
	ifeq("Pi1")
	$(error This is a multicore project Pi1 is not a valid target being single core)
	exit
	endif

######## PI1 NOT A VALID TARGET FOR THIS PROJECT #########
##Pi1: CFLAGS = -Wall -O3 -mcpu=arm1176jzf-s -mfpu=vfp -mfloat-abi=hard -ffreestanding -nostartfiles -std=gnu11 -mno-unaligned-access -fno-tree-loop-vectorize -fno-tree-slp-vectorize -Wno-nonnull-compare
##Pi1: ARMGNU = $(CROSS_COMPILER_ARM)/bin/arm-eabi
##Pi1: LINKERFILE = rpi32.ld
##Pi1: SMARTSTART = SmartStart32.S
##Pi1: IMGFILE = kernel.img

# The directory in which source files are stored.
SOURCE = ${CURDIR}
SOURCE_SDVBSCOMMON = ${CURDIR}/sdvbs/common
SOURCE_DISPARITY = ${CURDIR}/sdvbs/disparity

BUILD = Build


# The name of the assembler listing file to generate.
LIST = kernel.list

# The name of the map file to generate.
MAP = kernel.map

# The names of all object files that must be generated. Deduced from the 
# assembly code files in source.

ASMOBJS = $(patsubst $(SOURCE)/%.S,$(BUILD)/%.o,$(wildcard $(SOURCE)/*32.S))
ASMOBJS64 = $(patsubst $(SOURCE)/%.S,$(BUILD)/%.o,$(wildcard $(SOURCE)/*64.S))
COBJS = $(patsubst $(SOURCE)/%.c,$(BUILD)/%.o,$(wildcard $(SOURCE)/*.c))

COBJS_SDVBSCOMMON = $(patsubst $(SOURCE_SDVBSCOMMON)/%.c,$(BUILD)/%.o,$(wildcard $(SOURCE_SDVBSCOMMON)/*.c))
COBJS_DISPARITY = $(patsubst $(SOURCE_DISPARITY)/%.c,$(BUILD)/%.o,$(wildcard $(SOURCE_DISPARITY)/*.c))

Pi3-64: $(RANDOM_SETS_H) kernel8.elf
BINARY = $(IMGFILE)
.PHONY: Pi3-64

Pi3: kernel.elf
BINARY = $(IMGFILE)
.PHONY: Pi3

Pi2: kernel.elf
BINARY = $(IMGFILE)
.PHONY: Pi2

##Pi1: kernel.elf
##BINARY = $(IMGFILE)
##.PHONY: Pi1

$(BUILD)/%.o: $(SOURCE)/%.s
	$(ARMGNU)-gcc -MMD -MP -g $(CFLAGS) -c  $< -o $@ -lc -lm -lgcc

$(BUILD)/%.o: $(SOURCE)/%.S
	$(ARMGNU)-gcc -MMD -MP -g $(CFLAGS) -c  $< -o $@ -lc -lm -lgcc

$(BUILD)/%.o: $(SOURCE)/%.c
	$(ARMGNU)-gcc -MMD -MP -g $(CFLAGS) -c  $< -o $@ -lc -lm -lgcc

$(BUILD)/%.o: $(SOURCE_SDVBSCOMMON)/%.c
	$(ARMGNU)-gcc -MMD -MP -g $(CFLAGS) -c  $< -o $@ -lc -lm -lgcc

$(BUILD)/%.o: $(SOURCE_DISPARITY)/%.c
	$(ARMGNU)-gcc -MMD -MP -g $(CFLAGS) -c  $< -o $@ -lc -lm -lgcc

kernel8.elf: $(ASMOBJS64) $(COBJS) $(COBJS_SDVBSCOMMON) $(COBJS_DISPARITY)
	$(ARMGNU)-gcc -g $(CFLAGS) $(ASMOBJS64) $(COBJS) $(COBJS_SDVBSCOMMON) $(COBJS_DISPARITY) -T $(LINKERFILE) -Wl,--build-id=none -o $@ -lc -lm -lgcc
	$(ARMGNU)-objdump -d $@ > $(LIST)
	$(ARMGNU)-objcopy $@ -O binary DiskImg/$(BINARY)
	$(ARMGNU)-nm -n $@ > $(MAP)

kernel.elf: $(ASMOBJS) $(COBJS) 
	$(ARMGNU)-gcc -g $(CFLAGS) $(ASMOBJS) $(COBJS) -T $(LINKERFILE) -Wl,--build-id=none -o $@ -lc -lm -lgcc
	$(ARMGNU)-objdump -d $@ > $(LIST)
	$(ARMGNU)-objcopy $@ -O binary DiskImg/$(BINARY)
	$(ARMGNU)-nm -n $@ > $(MAP)

# Control silent mode  .... we want silent in clean
.SILENT: clean

# cleanup temp files
clean:
	$(RM) $(RANDOM_SETS_H) 
	$(RM) $(MAP) 
	$(RM) kernel.elf 
	$(RM) kernel8.elf
	$(RM) $(LIST) 
	$(RM) $(BUILD)$(SLASH)*.o 
	$(RM) $(BUILD)$(SLASH)*.d 
	echo CLEAN COMPLETED
.PHONY: clean

