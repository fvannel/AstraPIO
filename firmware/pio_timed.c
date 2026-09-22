/* SPDX-License-Identifier: Apache-2.0 */
#include "pio_timed.h"
int pio_timed_probe(pio_device *d) {
    uint16_t v; int rc;
    if ((rc = pio_read(d, 0x60, &v))) return rc;
    if (v != 0x5449) return PIO_EABI;
    if ((rc = pio_read(d, 0x6c, &v))) return rc;
    return v == 0x0118 ? PIO_OK : PIO_EABI;
}
int pio_timed_configure(pio_device *d, const pio_timed_config *c) {
    uint16_t v; int rc;
    if (!c || !c->idle_cycles || c->input_pin > 12 || c->output_pin > 13 ||
        c->prefix_bits < 1 || c->prefix_bits > 24 || c->sample_cycles < 1 ||
        c->launch_cycles <= c->sample_cycles || c->launch_cycles > 63 ||
        c->zero_cycles < 1 || c->zero_cycles > 63 ||
        c->one_cycles < 1 || c->one_cycles > 63) return PIO_EINVAL;
    if ((rc = pio_timed_probe(d))) return rc;
    if ((rc = pio_timed_control(d, PIO_TIMED_CLEAR))) return rc;
    const uint16_t values[] = {
        (uint16_t)(c->input_pin | (c->output_pin << 4)), c->idle_cycles,
        (uint16_t)(c->sample_cycles | (c->launch_cycles << 8)),
        (uint16_t)(c->zero_cycles | (c->one_cycles << 8)), c->prefix_bits
    };
    for (unsigned i = 0; i < 5; i++) {
        if ((rc = pio_write(d, (uint8_t)(0x62+i), values[i]))) return rc;
        if ((rc = pio_read(d, (uint8_t)(0x62+i), &v))) return rc;
        if (v != values[i]) return PIO_EVERIFY;
    }
    if ((rc = pio_read(d, 0x6b, &v))) return rc;
    return v & 0x20 ? PIO_EFAULT : PIO_OK;
}
int pio_timed_control(pio_device *d, unsigned control) {
    uint16_t v; int rc;
    if (control & ~0x507u) return PIO_EINVAL;
    if ((rc = pio_write(d, 0x61, (uint16_t)control))) return rc;
    if ((rc = pio_read(d, 0x61, &v))) return rc;
    if (v != (control & 7)) return PIO_EVERIFY;
    if ((rc = pio_read(d, 0x6b, &v))) return rc;
    return v & 0x20 ? PIO_EFAULT : PIO_OK;
}
int pio_timed_stage(pio_device *d, uint32_t value) {
    uint16_t status, control, lo, hi; int rc;
    if (value > 0xffffffu) return PIO_EINVAL;
    if ((rc = pio_read(d, 0x6b, &status))) return rc;
    if (status & 0x20) return PIO_EFAULT;
    if (status & 8) return PIO_EFULL;
    if ((rc = pio_read(d, 0x61, &control))) return rc;
    if ((rc = pio_write(d, 0x67, (uint16_t)value))) return rc;
    if ((rc = pio_write(d, 0x68, (uint16_t)(value >> 16)))) return rc;
    if ((rc = pio_read(d, 0x67, &lo))) return rc;
    if ((rc = pio_read(d, 0x68, &hi))) return rc;
    if (((uint32_t)hi << 16 | lo) != value) return PIO_EVERIFY;
    if ((rc = pio_write(d, 0x61, (control & 7) | PIO_TIMED_COMMIT))) return rc;
    if ((rc = pio_read(d, 0x6b, &status))) return rc;
    return status & 0x20 ? PIO_EFAULT : PIO_OK;
}
int pio_timed_receive(pio_device *d, uint32_t *value, uint16_t *status) {
    uint16_t lo, hi; int rc;
    if (!value || !status) return PIO_EINVAL;
    if ((rc = pio_read(d, 0x6b, status))) return rc;
    if (!(*status & 4)) return PIO_EEMPTY;
    if ((rc = pio_read(d, 0x69, &lo))) return rc;
    if ((rc = pio_read(d, 0x6a, &hi))) return rc;
    if (hi > 255) return PIO_EVERIFY;
    *value = (uint32_t)hi << 16 | lo;
    return PIO_OK;
}
