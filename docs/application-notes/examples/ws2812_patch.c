/* SPDX-License-Identifier: Apache-2.0 */
#include "ws2812_patch.h"

int ws_patch_start(pio_device *d, uint32_t initial, uint32_t *last_staged) {
    uint16_t v;
    int rc;
    if (!last_staged || initial > 0xffffffu) return PIO_EINVAL;
    if ((rc = pio_probe(d))) return rc;
    if ((rc = pio_timed_probe(d))) return rc;
    if ((rc = pio_read(d, 0x02, &v))) return rc;
    if (v != 1) return PIO_EABI;
    if ((rc = pio_read(d, 0x0f, &v))) return rc;
    if (v != 0x1002) return PIO_EABI;
    if ((rc = pio_read(d, 0x06, &v))) return rc;
    if (v) return PIO_EFAULT;
    if ((rc = pio_read(d, 0x6b, &v))) return rc;
    if (v) return PIO_EFAULT; /* Do not silently discard a capture or commit. */
    if ((rc = pio_read(d, 0x10, &v))) return rc;
    if (v & 0x0101u) return PIO_EFAULT; /* I0 undriven; O8 exclusive. */

    const pio_timed_config cfg = {
        .idle_cycles = 15000,
        .input_pin = 0, .output_pin = 8, .prefix_bits = 24,
        .sample_cycles = 25, .launch_cycles = 32,
        .zero_cycles = 16, .one_cycles = 32
    };
    if ((rc = pio_timed_configure(d, &cfg))) return rc;
    if ((rc = pio_timed_stage(d, initial))) return rc;
    if ((rc = pio_timed_control(d,
            PIO_TIMED_ENABLE | PIO_TIMED_OUTPUT | PIO_TIMED_REPLACE))) return rc;
    *last_staged = initial;
    return PIO_OK;
}

int ws_patch_increment(pio_device *d, uint32_t *last_staged) {
    if (!last_staged || *last_staged > 0xffffffu) return PIO_EINVAL;
    uint32_t next = (*last_staged + 1u) & 0xffffffu;
    int rc = pio_timed_stage(d, next);
    if (rc == PIO_OK) *last_staged = next;
    return rc;
}
