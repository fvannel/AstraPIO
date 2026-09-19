SIM ?= icarus
TOPLEVEL_LANG = verilog
TOPLEVEL = pio_program
COCOTB_TEST_MODULES = test_program
PDK_ROOT ?= $(abspath ../../work/pdk)
VERILOG_SOURCES = $(abspath ../../src/pio_program.v) $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
COMPILE_ARGS += -DFUNCTIONAL
PROGRAM_WIDTH ?= 10
PROGRAM_FF ?= 0
COMPILE_ARGS += -Ppio_program.WIDTH=$(PROGRAM_WIDTH)
COMPILE_ARGS += -Ppio_program.FLIP_FLOPS=$(PROGRAM_FF)
SIM_BUILD = sim_build/width$(PROGRAM_WIDTH)_ff$(PROGRAM_FF)
include $(shell cocotb-config --makefiles)/Makefile.sim
