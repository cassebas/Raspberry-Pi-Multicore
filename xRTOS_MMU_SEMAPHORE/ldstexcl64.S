/**
 * write_bit_atomic
 *
 * arguments:
 * x0: nth-bit to set in memory location
 * x1: boolean value to write
 * x2: pointer to memory location where to store the value
 *
 * return:
 * w0: result of the store, 0 successful, 1 unsuccessful
 */
	.text

	.align 6

	.globl write_bit_atomic
write_bit_atomic:
	mrs x3, daif              // get DAIF flags
	msr daifset, #2           // disable IRQ
    ldaxr x4, [x2]            // load the value from memory
    mov x5, #1
	lsl x5, x5, x0
    cbnz x1, set_bit
    mvn x5, x5                // have to clear the bit
    and x6, x4, x5
    b store_excl_loop
set_bit:
    orr x6, x4, x5
    // have to first load-acquire exclusive
    // otherwise the store-release exclusive
    // instruction won't work
store_excl_loop:
	stlxr w0, x6, [x2]
	cbnz w0, store_excl_loop
	dmb ish
	msr daif, x3              // restore DAIF flags
	ret


/**
 * read_bit_atomic
 *
 * arguments:
 * x0: nth-bit to read from memory location
 * x1: pointer to memory location where the bit must be read
 *
 * return:
 * x0: boolean value representing the bit that was read
 */
	.text

	.align 6

	.globl read_bit_atomic
read_bit_atomic:
	mrs x2, daif              // get DAIF flags
	msr daifset, #2           // disable IRQ
    mov x5, #1
	lsl x5, x5, x0
    // have to first load-acquire exclusive
    ldaxr x4, [x1]
	dmb ish
    and x5, x4, x5
    lsr x0, x5, x0
	msr daif, x2              // restore DAIF flags
	ret


/**
 * read_atomic
 *
 * arguments:
 * x0: pointer to memory location where the bit must be read
 *
 * return:
 * x0: value read from memory
 */
	.text

	.align 6

	.globl read_atomic
read_atomic:
	mrs x2, daif              // get DAIF flags
	msr daifset, #2           // disable IRQ
    ldxr x4, [x0]
	dmb ish
    mov x0, x4
	msr daif, x2              // restore DAIF flags
	ret


/**
 * countdown - function to perform busy waiting, for the purpose of
               delaying the processor a specific amount of cycles
 *             IRQ is disabled before waiting
 * arguments:
 * x0: number to use for countdown till zero
 */
	.text

	.align 6

	.globl countdown
countdown:
	mrs x2, daif              // get DAIF flags
	msr daifset, #2           // disable IRQ
    mov x1, x0
countdown_loop:
    cbz x1, countdown_ret
    sub x1, x1, #1
    b countdown_loop
countdown_ret:
	msr daif, x2              // restore DAIF flags
    ret
