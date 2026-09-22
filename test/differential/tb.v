`timescale 1ns/1ps
module tb;
    reg clk, rst_n, write_enable, read_commit;
    reg [7:0] address;
    reg [15:0] write_v4, write_v5;
    reg [12:0] pins_in;
    reg [13:0] reserved_pins;
    wire [15:0] read_v4, read_v5;
    wire [13:0] claimed_v4, claimed_v5, pins_v4, pins_v5;
    wire [12:0] sampled_v4, sampled_v5;
    wire [7:0] oe_v4, oe_v5;
    wire irq_v4, irq_v5, valid_v4, valid_v5;
    pio_reference_v4 old_core (
        .clk(clk), .rst_n(rst_n), .address(address), .write_data(write_v4),
        .write_enable(write_enable), .read_commit(read_commit),
        .read_valid(valid_v4), .read_data(read_v4), .pins_in(pins_in),
        .reserved_pins(reserved_pins), .sampled_inputs(sampled_v4),
        .claimed_pins(claimed_v4), .pins_out(pins_v4), .pins_oe(oe_v4), .irq(irq_v4)
    );
    pio_single_core new_core (
        .clk(clk), .rst_n(rst_n), .address(address), .write_data(write_v5),
        .write_enable(write_enable), .read_commit(read_commit),
        .read_valid(valid_v5), .read_data(read_v5), .pins_in(pins_in),
        .reserved_pins(reserved_pins), .sampled_inputs(sampled_v5),
        .claimed_pins(claimed_v5), .pins_out(pins_v5), .pins_oe(oe_v5), .irq(irq_v5)
    );
endmodule
