SIM ?= icarus
TOPLEVEL_LANG = verilog
TOPLEVEL = pio_fifo
COCOTB_TEST_MODULES = test_fifo
VERILOG_SOURCES = $(abspath $(CURDIR)/../../src/pio_fifo.v)
FIFO_WIDTH ?= 8
FIFO_ADDR_BITS ?= 1
COMPILE_ARGS += -Ppio_fifo.WIDTH=$(FIFO_WIDTH) -Ppio_fifo.ADDR_BITS=$(FIFO_ADDR_BITS)
SIM_BUILD = sim_build/fifo-W$(FIFO_WIDTH)-A$(FIFO_ADDR_BITS)
include $(shell cocotb-config --makefiles)/Makefile.sim
