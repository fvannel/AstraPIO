// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// Sixteen-word program store, using characterized IHP standard cells only.
// Default storage: capture a request at N. ICGs enable one row at N+1; latches
// close at falling N+1. Data/address remain stable through edge N+2. No reset
// on payload: the core's initialized length hides old/unknown words.
// FLIP_FLOPS selects a synchronous payload, with the same public busy contract.
module pio_program #(parameter WIDTH = 16, parameter FLIP_FLOPS = 0) (
    input wire clk, rst_n, write_enable,
    input wire [3:0] write_address, read_address,
    input wire [WIDTH-1:0] write_data,
    output wire [WIDTH-1:0] read_data,
    output wire busy
);
    reg pending, finishing;
    reg [3:0] saved_address;
    reg [WIDTH-1:0] saved_data;
    wire [WIDTH-1:0] words [0:15];
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
    generate if (FLIP_FLOPS) begin : synchronous_store
        // Same request/busy contract; capture the saved request at N+1.
        // Keep the finishing cycle so the public write latency does not change.
        // Payload remains unreset and is hidden by the core's initialized length.
        reg [WIDTH-1:0] storage [0:15];
        always @(posedge clk) begin
            if (rst_n && pending)
                storage[saved_address] <= saved_data;
        end
        for (row = 0; row < 16; row = row + 1) begin : outputs
            assign words[row] = storage[row];
        end
    end else begin : latch_store
      for (row = 0; row < 16; row = row + 1) begin : rows
        wire row_clock;
        sg13g2_lgcp_1 gate_cell (
            .CLK(clk), .GATE(pending && saved_address == row), .GCLK(row_clock)
        );
        for (bit_index = 0; bit_index < WIDTH; bit_index = bit_index + 1) begin : bits
            sg13g2_dlhq_1 storage (
                .GATE(row_clock), .D(saved_data[bit_index]), .Q(words[row][bit_index])
            );
        end
      end
    end endgenerate
endmodule
