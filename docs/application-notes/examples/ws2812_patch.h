/* SPDX-License-Identifier: Apache-2.0 */
#ifndef APIO_WS2812_PATCH_H
#define APIO_WS2812_PATCH_H
#include "pio_timed.h"

/* AN APIO 001 example, not a board driver. CLK must be 50 MHz.
 * Serialize every call and all other accesses to this device.
 * start() requires a known global reset and DIN held low. On success keep
 * DIN low for at least 310 us before the first frame. The transport must
 * implement the timing and uncertain-error contract of pio_host.h.
 * last_staged is software state, NOT a readback of the active output word. */
int ws_patch_start(pio_device *, uint32_t initial, uint32_t *last_staged);

/* EFULL: keep the request in software and defer it; no increment accepted.
 * Any other failure: diagnose/resynchronize, do not retry blindly.
 * Success means staged for a frame boundary, not already displayed. */
int ws_patch_increment(pio_device *, uint32_t *last_staged);
#endif
