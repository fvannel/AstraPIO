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
  // Isolated study selector. Zero is the unchanged ABI-5 behavior.
  // tools/micro_variant.py records and materializes each experiment separately.
  localparam integer STUDY_FEATURES = 4;

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
  wire core_read_valid, core_irq, timed_irq, timed_out;
  wire [15:0] core_read_data, timed_read_data;
  wire timed_page = address[7:4] == 4'h6;
  wire [12:0] sampled_inputs;
  wire [13:0] reserved_pins, claimed_pins;
  assign read_data = timed_page ? timed_read_data : core_read_data;
  assign read_valid = timed_page ? 1'b1 : core_read_valid;
  assign irq = core_irq | timed_irq;
  wire [13:0] pins_out;
  wire [7:0] pins_oe;

  pio_spi #(.STUDY(STUDY_FEATURES)) spi (
      .clk(clk), .rst_n(core_reset_n),
      .sck(ui_in[0]), .mosi(ui_in[1]), .cs_n(ui_in[2]), .miso(miso),
      .address(address), .write_data(write_data), .write_enable(write_enable),
      .read_data(read_data), .read_valid(read_valid),
      .read_commit(read_commit), .read_busy(read_busy)
  );

  pio_single_core #(.STUDY(STUDY_FEATURES)) core (
      .clk(clk), .rst_n(core_reset_n), .address(address),
      .write_data(write_data), .write_enable(write_enable && !timed_page), .read_data(core_read_data),
      .read_commit(read_commit && !timed_page), .read_valid(core_read_valid),
      .pins_in({ui_in[7:3], uio_in}),
      .reserved_pins(reserved_pins), .sampled_inputs(sampled_inputs), .claimed_pins(claimed_pins),
      .pins_out(pins_out), .pins_oe(pins_oe), .irq(core_irq)
  );

  wire _unused_read_lock = read_busy; // No peer RX consumer in the single core.

  pio_timed #(.STUDY(STUDY_FEATURES)) timed_io (
      .clk(clk), .rst_n(core_reset_n), .inputs(sampled_inputs), .occupied(claimed_pins),
      .address(address[3:0]), .write_data(write_data), .write_enable(write_enable && timed_page),
      .read_data(timed_read_data), .claim(reserved_pins), .serial_out(timed_out), .irq(timed_irq)
  );
  wire [13:0] effective_pins = (pins_out & ~reserved_pins) | ({14{timed_out}} & reserved_pins);

  // Dedicated MISO is NOT tri-state: use a dedicated host SPI bus.
  assign uo_out  = active ? {effective_pins[13:8], irq, miso} : 8'b0;
  assign uio_out = active ? effective_pins[7:0] : 8'b0;
  assign uio_oe  = active ? (pins_oe | reserved_pins[7:0]) : 8'b0;

endmodule
