SIM ?= icarus
TOPLEVEL_LANG = verilog
TOPLEVEL = pio_fifo
COCOTB_TEST_MODULES = test_fifo
VERILOG_SOURCES = $(abspath $(CURDIR)/../../src/pio_fifo.v)
SIM_BUILD = sim_build/fifo
include $(shell cocotb-config --makefiles)/Makefile.sim
