// SPDX-License-Identifier: Apache-2.0
`default_nettype none

// Synchronous queue, no combinational empty bypass. Full + pop accepts push.
// Flush/reset invalidate storage without resetting every data bit.
module pio_fifo #(
    parameter WIDTH = 16,
    parameter ADDR_BITS = 2
) (
    input wire clk, rst_n, flush,
    input wire push, pop,
    input wire [WIDTH-1:0] data_in,
    output wire [WIDTH-1:0] data_out,
    output wire empty, full, push_ready,
    output reg [ADDR_BITS:0] level
);
    localparam DEPTH = 1 << ADDR_BITS;
    reg [WIDTH-1:0] storage [0:DEPTH-1];
    reg [ADDR_BITS-1:0] read_pointer, write_pointer;
    wire take = pop && !empty;
    wire put = push && push_ready;
    assign empty = level == 0;
    assign full = level == DEPTH;
    assign push_ready = !full || take;
    assign data_out = empty ? {WIDTH{1'b0}} : storage[read_pointer];

    always @(posedge clk) begin
        if (!rst_n || flush) begin
            read_pointer <= 0;
            write_pointer <= 0;
            level <= 0;
        end else begin
            if (put) begin
                storage[write_pointer] <= data_in;
                write_pointer <= write_pointer + 1'b1;
            end
            if (take)
                read_pointer <= read_pointer + 1'b1;
            case ({put, take})
                2'b10: level <= level + 1'b1;
                2'b01: level <= level - 1'b1;
                default: begin end
            endcase
        end
    end
endmodule
