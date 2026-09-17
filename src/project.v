/*
 * Copyright (c) 2026 Fabien
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// General-purpose PIO prototype. The target frequency and tile fit are unproven.
module tt_um_fabien_pio (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  wire active = ena & rst_n;
  // Asynchronous assertion releases the pads immediately; internal reset
  // deassertion crosses one shared two-flop synchronizer.
  (* async_reg = "true" *) reg [1:0] reset_release;
  always @(posedge clk or negedge active) begin
      if (!active) reset_release <= 0;
      else reset_release <= {reset_release[0], 1'b1};
  end
  wire core_reset_n = reset_release[1];
  wire [7:0] address;
  wire [15:0] write_data, read_data;
  wire write_enable, read_commit, read_busy, read_valid, miso, irq;
  wire [13:0] pins_out;
  wire [7:0] pins_oe;

  pio_spi spi (
      .clk(clk), .rst_n(core_reset_n),
      .sck(ui_in[0]), .mosi(ui_in[1]), .cs_n(ui_in[2]), .miso(miso),
      .address(address), .write_data(write_data), .write_enable(write_enable),
      .read_data(read_data), .read_valid(read_valid),
      .read_commit(read_commit), .read_busy(read_busy)
  );

  pio_core core (
      .clk(clk), .rst_n(core_reset_n), .address(address),
      .write_data(write_data), .write_enable(write_enable), .read_data(read_data),
      .read_commit(read_commit), .read_busy(read_busy), .read_valid(read_valid),
      .pins_in({ui_in[7:3], uio_in}),
      .pins_out(pins_out), .pins_oe(pins_oe), .irq(irq)
  );

  // Dedicated MISO is NOT tri-state: use a dedicated host SPI bus.
  assign uo_out  = active ? {pins_out[13:8], irq, miso} : 8'b0;
  assign uio_out = active ? pins_out[7:0] : 8'b0;
  assign uio_oe  = active ? pins_oe : 8'b0;

endmodule
