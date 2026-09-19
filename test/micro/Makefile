ROOT := $(abspath ../..)
VARIANT ?= baseline
SIM ?= icarus
TOPLEVEL_LANG = verilog
PDK_ROOT ?= $(ROOT)/work/pdk
RUN_DIR := $(ROOT)/work/micro/$(VARIANT)
SIM_BUILD = $(RUN_DIR)/sim_build
COCOTB_RESULTS_FILE = $(RUN_DIR)/results.xml
export PYTHONPATH := $(ROOT)/test:$(ROOT)/test/micro:$(ROOT)/tools:$(PYTHONPATH)
export ASTRA_VARIANT = $(VARIANT)
COMPILE_ARGS += -DFUNCTIONAL
VERILOG_SOURCES = $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
VERILOG_SOURCES += $(addprefix $(ROOT)/src/,project.v pio_spi.v pio_single_core.v pio_program.v pio_fifo.v pio_timed.v)
VERILOG_SOURCES += $(ROOT)/test/tb.v
TOPLEVEL = tb
COCOTB_TEST_MODULES ?= test_micro
include $(shell cocotb-config --makefiles)/Makefile.sim
