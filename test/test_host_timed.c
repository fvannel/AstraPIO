/* SPDX-License-Identifier: Apache-2.0 */
#include "../firmware/pio_timed.h"
#include <assert.h>
#include <string.h>

/* Bus-boundary model. RTL timing/atomicity is independently checked by the
 * cocotb pin-level suite, not inferred from this model. */
typedef struct {
    uint16_t reg[256];
    unsigned calls, fail_at, commit_count, ack_count;
} bus;
static int transfer(void *ctx, const uint8_t tx[4], uint8_t rx[4]) {
    bus *b = ctx;
    if (++b->calls == b->fail_at) return -1;
    uint8_t a = tx[1];
    uint16_t value = (uint16_t)((uint16_t)tx[2] << 8) | tx[3];
    memset(rx, 0, 4);
    if (tx[0] == 2) {
        if (a == 0x61) {
            b->reg[a] = value & 7;
            if (value & 0x400) b->reg[0x6b] &= ~0xe0;
            if (value & 0x100) { b->ack_count++; b->reg[0x6b] &= ~4; }
            if (value & 0x200) { b->commit_count++; b->reg[0x6b] |= 8; }
        } else b->reg[a] = value;
    } else {
        assert(tx[0] == 3);
        value = b->reg[a];
        rx[2] = (uint8_t)(value >> 8); rx[3] = (uint8_t)value;
    }
    return 0;
}
int main(void) {
    bus b = {0}; pio_device d = {transfer, &b};
    pio_timed_config c = {15000, 0, 8, 24, 25, 32, 16, 32};
    assert(pio_timed_probe(&d) == PIO_EABI); /* Existing chip must be rejected. */
    b.reg[0x60] = 0x5449; b.reg[0x6c] = 0x0118;
    assert(pio_timed_probe(&d) == PIO_OK);
    assert(pio_timed_configure(&d, &c) == PIO_OK);
    assert(b.reg[0x61] == 0 && b.reg[0x62] == 0x80);
    assert(b.reg[0x63] == 15000 && b.reg[0x64] == 0x2019);
    assert(b.reg[0x65] == 0x2010 && b.reg[0x66] == 24);
    c.prefix_bits = 25;
    unsigned calls = b.calls;
    assert(pio_timed_configure(&d, &c) == PIO_EINVAL && b.calls == calls);
    assert(pio_timed_stage(&d, 0x123456) == PIO_OK);
    assert(b.reg[0x67] == 0x3456 && b.reg[0x68] == 0x12 && b.commit_count == 1);
    assert(pio_timed_stage(&d, 0xABCDEF) == PIO_EFULL && b.commit_count == 1);
    b.reg[0x6b] = 0;
    assert(pio_timed_control(&d, 7) == PIO_OK && b.reg[0x61] == 7);
    assert(pio_timed_stage(&d, 0xABCDEF) == PIO_OK && b.reg[0x61] == 7);
    b.reg[0x6b] = 0x44; b.reg[0x69] = 0x2233; b.reg[0x6a] = 0x11;
    uint32_t value = 0; uint16_t status = 0;
    assert(pio_timed_receive(&d, &value, &status) == PIO_OK);
    assert(value == 0x112233 && status == 0x44 && b.ack_count == 0);
    assert(pio_timed_control(&d, 7|PIO_TIMED_ACK|PIO_TIMED_CLEAR) == PIO_OK);
    assert(b.ack_count == 1 && b.reg[0x6b] == 0 && b.reg[0x61] == 7);
    assert(pio_timed_receive(&d, &value, &status) == PIO_EEMPTY);
    assert(pio_timed_receive(&d, 0, &status) == PIO_EINVAL);
    assert(pio_timed_stage(&d, 0x1000000) == PIO_EINVAL);
    assert(pio_timed_control(&d, PIO_TIMED_COMMIT) == PIO_EINVAL);
    /* Every failed SPI transaction must stop the operation without retrying. */
    for (unsigned fail = 1; fail <= 8; fail++) {
        bus fault = {0}; pio_device f = {transfer, &fault};
        fault.fail_at = fail;
        assert(pio_timed_stage(&f, 1) == PIO_EIO);
        assert(fault.calls == fail);
    }
    return 0;
}
