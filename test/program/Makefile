SIM ?= icarus
TOPLEVEL_LANG = verilog
TOPLEVEL = pio_program
COCOTB_TEST_MODULES = test_program
PDK_ROOT ?= $(abspath ../../work/pdk)
VERILOG_SOURCES = $(abspath ../../src/pio_program.v) $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
COMPILE_ARGS += -DFUNCTIONAL
PROGRAM_WIDTH ?= 10
COMPILE_ARGS += -Ppio_program.WIDTH=$(PROGRAM_WIDTH)
SIM_BUILD = sim_build/width$(PROGRAM_WIDTH)
include $(shell cocotb-config --makefiles)/Makefile.sim
