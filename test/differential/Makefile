SIM ?= icarus
TOPLEVEL_LANG = verilog
TOPLEVEL = tb
COCOTB_TEST_MODULES = test_equivalence
PDK_ROOT ?= $(abspath ../../vendor/ihp-open-pdk)
VERILOG_SOURCES = $(abspath tb.v pio_reference_v4.v ../../src/pio_single_core.v ../../src/pio_program.v ../../src/pio_fifo.v) $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
COMPILE_ARGS += -DFUNCTIONAL
SIM_BUILD = sim_build
include $(shell cocotb-config --makefiles)/Makefile.sim
