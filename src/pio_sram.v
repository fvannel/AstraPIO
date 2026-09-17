// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// One-cycle byte SRAM. Program and queue ownership is enforced in pio_core.
module pio_sram (
    input wire clk, rst_n, write_enable,
    input wire [7:0] address, data_in,
    output wire [7:0] data_out
);
`ifdef PIO_IHP_SRAM
    // Isolate the macro's characterized output-load limit and drive its address
    // pins explicitly. These are ordinary PDK standard cells, not PDK edits.
    wire [7:0] buffered_address, macro_data;
    genvar bit_index;
    generate for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin : interface_buffers
        (* keep = 1 *) sg13g2_buf_4 address_buffer (.A(address[bit_index]), .X(buffered_address[bit_index]));
        (* keep = 1 *) sg13g2_buf_4 data_buffer (.A(macro_data[bit_index]), .X(data_out[bit_index]));
    end endgenerate
    RM_IHPSG13_1P_256x8_c3_bm_bist sram (
        .A_CLK(clk), .A_MEN(rst_n), .A_WEN(write_enable), .A_REN(!write_enable),
        .A_ADDR(buffered_address), .A_DIN(data_in), .A_DOUT(macro_data), .A_BM(8'hff),
        .A_DLY(1'b1), .A_BIST_CLK(1'b0), .A_BIST_EN(1'b0),
        .A_BIST_MEN(1'b0), .A_BIST_WEN(1'b0), .A_BIST_REN(1'b0),
        .A_BIST_ADDR(8'b0), .A_BIST_DIN(8'b0), .A_BIST_BM(8'b0)
    );
`else
    reg [7:0] memory [0:255];
    reg [7:0] output_byte;
    assign data_out = output_byte;
    always @(posedge clk) begin
        if (rst_n) begin
            if (write_enable) memory[address] <= data_in;
            else output_byte <= memory[address];
        end
    end
`endif
endmodule
