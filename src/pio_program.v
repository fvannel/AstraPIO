// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// Shared 16 x 16 program store, using characterized IHP standard cells only.
// Capture a request at edge N. ICGs enable exactly one row at N+1; its latches
// close at falling N+1. Data/address remain stable through edge N+2. No reset
// on payload: the core's initialized length hides old/unknown words.
module pio_program (
    input wire clk, rst_n, write_enable,
    input wire [3:0] write_address, read_address,
    input wire [15:0] write_data,
    output wire [15:0] read_data,
    output wire busy
);
    reg pending, finishing;
    reg [3:0] saved_address;
    reg [15:0] saved_data;
    wire [15:0] words [0:15];
    assign busy = pending | finishing;
    assign read_data = words[read_address];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pending <= 0;
            finishing <= 0;
        end else begin
            pending <= write_enable && !busy;
            finishing <= pending;
        end
    end
    always @(posedge clk) begin
        if (rst_n && write_enable && !busy) begin
            saved_address <= write_address;
            saved_data <= write_data;
        end
    end
    genvar row, bit_index;
    generate for (row = 0; row < 16; row = row + 1) begin : rows
        wire row_clock;
        sg13g2_lgcp_1 gate_cell (
            .CLK(clk), .GATE(pending && saved_address == row), .GCLK(row_clock)
        );
        for (bit_index = 0; bit_index < 16; bit_index = bit_index + 1) begin : bits
            sg13g2_dlhq_1 storage (
                .GATE(row_clock), .D(saved_data[bit_index]), .Q(words[row][bit_index])
            );
        end
    end endgenerate
endmodule
