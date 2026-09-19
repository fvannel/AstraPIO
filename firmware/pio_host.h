/* SPDX-License-Identifier: Apache-2.0 */
#ifndef PIO_HOST_H
#define PIO_HOST_H
#include <stddef.h>
#include <stdint.h>

/* Transport owns ONE mode-0, MSB-first, 32-clock CS assertion per call.
 * SCK high/low and CS setup/hold/gap >= 6 ASIC clock periods. Return 0 on
 * success; do not silently retry destructive RX reads after uncertain errors.
 * Callback may use LPC546xx SPI/DMA, but must wait for wire completion + CS gap.
 * All calls on one device must be serialized (including ISR/DMA access).
 */
typedef int (*pio_transfer_fn)(void *ctx, const uint8_t tx[4], uint8_t rx[4]);
typedef struct { pio_transfer_fn transfer; void *ctx; } pio_device;
enum { PIO_OK=0, PIO_EINVAL=-1, PIO_EIO=-2, PIO_EABI=-3,
       PIO_EVERIFY=-4, PIO_EEMPTY=-5, PIO_EFULL=-6, PIO_EFAULT=-7 };
int pio_read(pio_device *, uint8_t address, uint16_t *value);
int pio_write(pio_device *, uint8_t address, uint16_t value);
int pio_probe(pio_device *);
int pio_stop(pio_device *); /* Stops the context; GPIO levels are retained. */
/* ABI v5 only; ten-bit program words in uint16_t containers (upper bits zero).
 * All context arguments must be zero; run mask must be 0 or 1.
 * Reload resets the sole context and its queues. Probe rejects v3/v4 hardware. */
int pio_load(pio_device *, const uint16_t *words, size_t count);
int pio_set_entry(pio_device *, unsigned context, unsigned pc);
int pio_set_mask(pio_device *, unsigned context, uint16_t global_mask);
int pio_run(pio_device *, unsigned context_mask);
int pio_push(pio_device *, unsigned context, uint8_t byte);
/* One credit read, then up to 2 writes; preferred for sustained TX streams.
 * *sent counts certainly completed writes; on PIO_EIO the failing transaction
 * may still have reached hardware, so the application must resynchronize. */
int pio_push_many(pio_device *, unsigned context, const uint8_t *, size_t count, size_t *sent);
int pio_pop(pio_device *, unsigned context, uint8_t *byte);
#endif
