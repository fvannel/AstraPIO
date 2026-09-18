/* SPDX-License-Identifier: Apache-2.0 */
#ifndef PIO_TIMED_H
#define PIO_TIMED_H
#include "pio_host.h"

/* EXPERIMENTAL: requires timed extension identity 0x5449 / version 0x0118.
 * This extension is NOT present in the submitted compact 946648ff chip.
 * Serialize ALL calls on a device. The board-specific SPI/DMA callback and
 * electrical interface are supplied by the application and not tested here. */
typedef struct {
    uint16_t idle_cycles;
    uint8_t input_pin, output_pin, prefix_bits;
    uint8_t sample_cycles, launch_cycles, zero_cycles, one_cycles;
} pio_timed_config;
enum { PIO_TIMED_ENABLE=1, PIO_TIMED_OUTPUT=2, PIO_TIMED_REPLACE=4,
       PIO_TIMED_ACK=0x100, PIO_TIMED_COMMIT=0x200, PIO_TIMED_CLEAR=0x400 };
int pio_timed_probe(pio_device *);
/* Disables the engine and verifies configuration. Does not start it. */
int pio_timed_configure(pio_device *, const pio_timed_config *);
/* Mode bits 0..2 plus explicit ACK/CLEAR flags. COMMIT belongs to stage(). */
int pio_timed_control(pio_device *, unsigned control);
/* Atomically stages a 24-bit value for the next qualified frame. EFULL means
 * an earlier commit is still pending. EIO has an uncertain effect: never retry
 * blindly or advance the software counter on error. */
int pio_timed_stage(pio_device *, uint32_t value);
/* Non-destructive stable prefix read. Returns status (including overrun) to
 * caller; acknowledge only AFTER the application has accepted the word. */
int pio_timed_receive(pio_device *, uint32_t *value, uint16_t *status);
#endif
