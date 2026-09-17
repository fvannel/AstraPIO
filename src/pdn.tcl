# SPDX-License-Identifier: Apache-2.0
# Preserve the TT grid; the SRAM has its power access on Metal4, not TopMetal2.
source $::env(SCRIPTS_DIR)/openroad/common/pdn_cfg.tcl
add_pdn_connect -grid macro -layers "Metal4 TopMetal1"
