# Replay the WS2812 application without changing the release simulation inputs.
ROOT := $(abspath ../..)
MODE ?= rtl
SIM ?= icarus
TOPLEVEL_LANG = verilog
PDK_ROOT ?= $(ROOT)/vendor/ihp-open-pdk
GL_NETLIST ?= $(ROOT)/release/tt_um_fabien_pio.v
RUN_DIR ?= $(ROOT)/work/ws2812-counter-replay/$(MODE)
SIM_BUILD = $(RUN_DIR)/sim_build
COCOTB_RESULTS_FILE = $(RUN_DIR)/results.xml
export ASTRA_WS_REPORT = $(RUN_DIR)/counter-report.json
export ASTRA_WS_MODE = $(MODE)
export PYTHONPATH := $(ROOT)/test:$(PYTHONPATH)
COMPILE_ARGS += -DFUNCTIONAL
VERILOG_SOURCES = $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
ifeq ($(MODE),gl)
COMPILE_ARGS += -DGL_TEST -DSIM
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v $(GL_NETLIST)
else ifeq ($(MODE),rtl)
VERILOG_SOURCES += $(addprefix $(ROOT)/src/,project.v pio_spi.v pio_single_core.v pio_program.v pio_fifo.v pio_timed.v)
else
$(error MODE must be rtl or gl)
endif
VERILOG_SOURCES += $(ROOT)/test/tb.v
TOPLEVEL = tb
COCOTB_TEST_MODULES = test_timed,test_ws2812_counter
FST = -fst
include $(shell cocotb-config --makefiles)/Makefile.sim
