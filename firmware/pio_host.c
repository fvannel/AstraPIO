/* SPDX-License-Identifier: Apache-2.0 */
#include "pio_host.h"

int pio_read(pio_device *d, uint8_t address, uint16_t *value) {
    uint8_t tx[4] = {3, address, 0, 0}, rx[4];
    if (!d || !d->transfer || !value) return PIO_EINVAL;
    if (d->transfer(d->ctx, tx, rx)) return PIO_EIO;
    *value = (uint16_t)((uint16_t)rx[2] << 8) | rx[3];
    return PIO_OK;
}
int pio_write(pio_device *d, uint8_t address, uint16_t value) {
    uint8_t tx[4] = {2, address, (uint8_t)(value >> 8), (uint8_t)value}, rx[4];
    if (!d || !d->transfer) return PIO_EINVAL;
    return d->transfer(d->ctx, tx, rx) ? PIO_EIO : PIO_OK;
}
int pio_probe(pio_device *d) {
    uint16_t value;
    int rc = pio_read(d, 0, &value);
    if (rc) return rc;
    if (value != 0x5049) return PIO_EABI;
    rc = pio_read(d, 1, &value);
    return rc ? rc : value == 0x0300 ? PIO_OK : PIO_EABI;
}
int pio_stop(pio_device *d) { return pio_write(d, 3, 0); }

int pio_load(pio_device *d, const uint16_t *words, size_t count) {
    uint16_t value;
    int rc;
    if (!words || count == 0 || count > 16) return PIO_EINVAL;
    if ((rc = pio_probe(d))) return rc;
    if ((rc = pio_stop(d))) return rc;
    if ((rc = pio_write(d, 4, 3))) return rc;
    if ((rc = pio_write(d, 0x0a, 0))) return rc;
    for (size_t i = 0; i < count; ++i) {
        if ((rc = pio_write(d, (uint8_t)(0x40+i), words[i]))) return rc;
        if ((rc = pio_read(d, (uint8_t)(0x40+i), &value))) return rc;
        if (value != words[i]) return PIO_EVERIFY;
    }
    if ((rc = pio_read(d, 6, &value))) return rc;
    return value ? PIO_EFAULT : PIO_OK;
}
int pio_set_entry(pio_device *d, unsigned c, unsigned pc) {
    uint16_t value;
    int rc;
    if (c > 1 || pc > 15) return PIO_EINVAL;
    if ((rc = pio_read(d, 3, &value))) return rc;
    if (value & (1u << c)) return PIO_EFAULT;
    if ((rc = pio_write(d, (uint8_t)(0x11+16*c), (uint16_t)pc))) return rc;
    if ((rc = pio_read(d, (uint8_t)(0x11+16*c), &value))) return rc;
    return value == pc ? PIO_OK : PIO_EVERIFY;
}
int pio_set_mask(pio_device *d, unsigned c, uint16_t mask) {
    uint16_t actual;
    int rc;
    if (c > 1 || (mask & (c ? 0xc07fu : 0xff80u))) return PIO_EINVAL;
    if ((rc = pio_read(d, 3, &actual))) return rc;
    if (actual) return PIO_EFAULT;
    if ((rc = pio_write(d, (uint8_t)(0x10 + 16*c), mask))) return rc;
    if ((rc = pio_read(d, (uint8_t)(0x10 + 16*c), &actual))) return rc;
    return actual == mask ? PIO_OK : PIO_EVERIFY;
}
int pio_run(pio_device *d, unsigned mask) {
    uint16_t errors;
    int rc;
    if (mask > 3) return PIO_EINVAL;
    if ((rc = pio_read(d, 6, &errors))) return rc;
    if (errors) return PIO_EFAULT;
    return pio_write(d, 3, (uint16_t)mask);
}
int pio_push(pio_device *d, unsigned c, uint8_t byte) {
    uint16_t status;
    int rc;
    if (c > 1) return PIO_EINVAL;
    if ((rc = pio_read(d, (uint8_t)(0x16 + 16*c), &status))) return rc;
    if (status & 2) return PIO_EFULL;
    return pio_write(d, (uint8_t)(0x14 + 16*c), byte);
}
int pio_pop(pio_device *d, unsigned c, uint8_t *byte) {
    uint16_t value;
    int rc;
    if (c > 1 || !byte) return PIO_EINVAL;
    if ((rc = pio_read(d, (uint8_t)(0x15 + 16*c), &value))) return rc;
    if (!(value & 0x8000)) return PIO_EEMPTY;
    *byte = (uint8_t)value;
    return PIO_OK;
}
int pio_push_many(pio_device *d, unsigned c, const uint8_t *bytes, size_t count, size_t *sent) {
    uint16_t status;
    int rc;
    if (!sent) return PIO_EINVAL;
    *sent = 0;
    if (c > 1 || (!bytes && count)) return PIO_EINVAL;
    if (!count) return PIO_OK;
    if ((rc = pio_read(d, (uint8_t)(0x16 + 16*c), &status))) return rc;
    unsigned level = (status >> 12) & 3;
    if (level > 2) return PIO_EVERIFY;
    size_t available = 2 - level;
    if (!available) return PIO_EFULL;
    if (count > available) count = available;
    while (*sent < count) {
        if ((rc = pio_write(d, (uint8_t)(0x14 + 16*c), bytes[*sent]))) return rc;
        ++*sent;
    }
    return PIO_OK;
}
