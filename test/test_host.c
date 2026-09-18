#include "../firmware/pio_host.h"
#include <assert.h>
#include <string.h>
typedef struct { uint16_t reg[256], memory[128]; int fail, corrupt; unsigned calls; } mock;
static int transfer(void *ctx, const uint8_t tx[4], uint8_t rx[4]) {
    mock *m = ctx;
    uint8_t a = tx[1];
    uint16_t v = (uint16_t)((uint16_t)tx[2] << 8) | tx[3];
    m->calls++;
    if (m->fail) return -1;
    memset(rx, 0, 4);
    if (tx[0] == 2) {
        if (a >= 0x40 && a <= 0x4f) m->memory[a-0x40] = v;
        else m->reg[a] = v;
    } else {
        assert(tx[0] == 3);
        v = a >= 0x40 && a <= 0x4f ? m->memory[a-0x40] : m->reg[a];
        if (m->corrupt && a >= 0x40 && a <= 0x4f) v ^= 1;
        rx[2] = (uint8_t)(v >> 8); rx[3] = (uint8_t)v;
    }
    return 0;
}
int main(void) {
    mock m = {0}; pio_device d = {transfer, &m}; uint8_t b = 0;
    uint16_t code[16]; for (unsigned i=0; i<16; i++) code[i] = (uint16_t)(0xa000+i);
    m.reg[0]=0x5049; m.reg[1]=0x0300;
    assert(pio_probe(&d)==0);
    assert(pio_load(&d, code, 16)==0);
    assert(!memcmp(m.memory, code, sizeof code));
    assert(m.reg[3]==0 && m.reg[4]==3 && m.reg[0x0a]==0);
    assert(pio_set_entry(&d,1,7)==0 && m.reg[0x21]==7);
    assert(pio_set_mask(&d, 0, 0x100)==PIO_EINVAL);
    assert(pio_set_mask(&d, 1, 0x100)==0);
    assert(pio_run(&d, 3)==0 && m.reg[3]==3);
    m.reg[0x16]=0x2002; assert(pio_push(&d,0,0x55)==PIO_EFULL);
    m.reg[0x16]=0; assert(pio_push(&d,0,0x55)==0 && m.reg[0x14]==0x55);
    uint8_t bytes[3]={1,2,3}; size_t sent=99;
    m.reg[0x16]=0;
    assert(pio_push_many(&d,0,bytes,3,&sent)==0 && sent==2 && m.reg[0x14]==2);
    m.reg[0x16]=0x2002; assert(pio_push_many(&d,0,bytes,3,&sent)==PIO_EFULL && sent==0);
    assert(pio_pop(&d,0,&b)==PIO_EEMPTY);
    m.reg[0x15]=0x809a; assert(pio_pop(&d,0,&b)==0 && b==0x9a);
    m.corrupt=1; assert(pio_load(&d,code,1)==PIO_EVERIFY); m.corrupt=0;
    m.reg[1]=0x0200; assert(pio_load(&d,code,1)==PIO_EABI); m.reg[1]=0x0300;
    m.reg[6]=1; assert(pio_run(&d,1)==PIO_EFAULT); m.reg[6]=0;
    m.fail=1; assert(pio_probe(&d)==PIO_EIO);
    assert(pio_read(0,0,code)==PIO_EINVAL);
    assert(pio_load(&d,code,17)==PIO_EINVAL);
    assert(pio_set_entry(&d,2,0)==PIO_EINVAL);
    return 0;
}
