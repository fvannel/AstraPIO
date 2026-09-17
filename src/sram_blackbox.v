// SPDX-License-Identifier: Apache-2.0
// Lint-only interface, matching IHP Open PDK c4b8b4e SRAM model.
// Simulation uses the actual PDK behavioral model, not this blackbox.
(* blackbox *)
module RM_IHPSG13_1P_256x8_c3_bm_bist (
    input A_CLK, A_MEN, A_WEN, A_REN,
    input [7:0] A_ADDR,
    input [7:0] A_DIN,
    input A_DLY,
    output [7:0] A_DOUT,
    input [7:0] A_BM,
    input A_BIST_CLK, A_BIST_EN, A_BIST_MEN, A_BIST_WEN, A_BIST_REN,
    input [7:0] A_BIST_ADDR,
    input [7:0] A_BIST_DIN, A_BIST_BM
);
endmodule
