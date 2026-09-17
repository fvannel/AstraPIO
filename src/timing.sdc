# Retain all official IO loads/delays, fanout, slew, derates and propagated clocks.
source $::env(SCRIPTS_DIR)/base.sdc
# Engineering assumptions, NOT measured board-clock specifications:
# setup includes cycle-to-cycle jitter (250 ps); same-edge hold jitter is
# correlated, with 50 ps residual uncertainty. Actual CTS skew and the base
# +/-5% early/late derates remain active. No data paths are false-pathed.
# Qualification of these assumptions is a release blocker: docs/toolchain.md.
set_clock_uncertainty -setup 0.25 [get_clocks clk]
set_clock_uncertainty -hold 0.05 [get_clocks clk]
