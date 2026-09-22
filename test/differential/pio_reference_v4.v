// Frozen behavioral comparison reference from commit 9ac64fb.
// Only the module name is changed; never include this file in the ASIC sources.
// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// ABI v4: one context, 16 program words, two-byte TX and RX queues.
// Preserve the v3 4-clock instruction cadence: fetch, execute, idle, idle.
module pio_reference_v4 (
    input wire clk, rst_n,
    input wire [7:0] address,
    input wire [15:0] write_data,
    input wire write_enable, read_commit,
    output wire read_valid,
    output reg [15:0] read_data,
    input wire [12:0] pins_in,
    input wire [13:0] reserved_pins,
    output wire [12:0] sampled_inputs,
    output wire [13:0] claimed_pins,
    output reg [13:0] pins_out,
    output reg [7:0] pins_oe,
    output wire irq
);
    reg [4:0] program_length, pc;
    reg [7:0] accumulator, delay_slots;
    reg [3:0] counter;
    reg [13:0] output_mask;
    reg running, fault, irq_pending, event_flag, rx_irq_mask, host_error;
    reg [1:0] phase;
    reg fetched_valid;
    reg [15:0] instruction;
    (* async_reg = "true" *) reg [12:0] input_meta, input_sync;
    assign sampled_inputs = input_sync;
    assign claimed_pins = output_mask;
    wire memory_busy;
    wire [15:0] program_q;
    wire program_page = address[7:4] == 4'h4;
    wire legal_program_write = !running && !memory_busy &&
        {1'b0,address[3:0]} <= program_length;
    wire restart = write_enable && address == 4 && write_data == 1;
    wire host_run = write_enable && address == 3 && write_data <= 1;
    wire control_this_slot = restart || host_run;
    wire slot = phase == 1 && fetched_valid && running && !control_this_slot;
    wire executing = slot && delay_slots == 0 && pc < program_length;
    pio_program imem (
        .clk(clk), .rst_n(rst_n),
        .write_enable(write_enable && program_page && legal_program_write),
        .write_address(address[3:0]), .write_data(write_data),
        .read_address(running ? pc[3:0] : address[3:0]),
        .read_data(program_q), .busy(memory_busy)
    );
    always @(posedge clk) if (phase == 0) instruction <= program_q;
    wire tx_empty, tx_full, tx_ready, rx_empty, rx_full, rx_ready;
    wire [7:0] tx_q, rx_q;
    wire [1:0] tx_level, rx_level;
    wire host_tx = write_enable && address == 8'h14;
    wire pull = executing && instruction == 16'hf000 && !tx_empty && !restart;
    wire push = executing && instruction == 16'hf100 && rx_ready && !restart;
    // There is no peer consumer: the SPI snapshot remains the RX head until
    // the transport commits a complete, valid read. Empty reads cannot pop.
    pio_fifo #(.WIDTH(8), .ADDR_BITS(1)) tx (
        .clk(clk), .rst_n(rst_n), .flush(restart), .push(host_tx), .pop(pull),
        .data_in(write_data[7:0]), .data_out(tx_q), .empty(tx_empty),
        .full(tx_full), .push_ready(tx_ready), .level(tx_level)
    );
    pio_fifo #(.WIDTH(8), .ADDR_BITS(1)) rx (
        .clk(clk), .rst_n(rst_n), .flush(restart), .push(push),
        .pop(read_commit && address == 8'h15), .data_in(accumulator),
        .data_out(rx_q), .empty(rx_empty), .full(rx_full),
        .push_ready(rx_ready), .level(rx_level)
    );
    assign read_valid = address != 8'h15 || !rx_empty;
    assign irq = irq_pending || fault || host_error || (rx_irq_mask && !rx_empty);
    always @* begin
        read_data = 0;
        if (program_page) begin
            if (!running && !memory_busy && {1'b0,address[3:0]} < program_length)
                read_data = program_q;
        end else case (address)
            8'h00: read_data = 16'h5049;
            8'h01: read_data = 16'h0400;
            8'h02: read_data = 1;
            8'h03: read_data = {15'b0,running};
            8'h05: read_data = {15'b0,irq_pending};
            8'h06: read_data = {7'b0,fault,7'b0,host_error};
            8'h07: read_data = {2'b0,pins_out};
            8'h08: read_data = {8'b0,pins_oe};
            8'h09: read_data = {3'b0,input_sync};
            8'h0a, 8'h1f: read_data = {11'b0,program_length};
            8'h0b: read_data = {15'b0,memory_busy};
            8'h0c: read_data = {15'b0,rx_irq_mask};
            8'h0d, 8'h0e: read_data = {15'b0,event_flag};
            8'h0f: read_data = 16'h1002;
            8'h10: read_data = {2'b0,output_mask};
            8'h11: read_data = {11'b0,pc};
            8'h12: read_data = {8'b0,accumulator};
            8'h13: read_data = {8'b0,delay_slots};
            8'h15: read_data = {~rx_empty,7'b0,rx_q};
            8'h16: read_data = {rx_level,tx_level,8'b0,rx_full,rx_empty,tx_full,tx_empty};
            8'h17: read_data = {12'b0,counter};
            default: read_data = 0;
        endcase
    end
    integer p;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            program_length <= 0; pc <= 0; accumulator <= 0; delay_slots <= 0;
            counter <= 0; output_mask <= 0; running <= 0; fault <= 0;
            irq_pending <= 0; event_flag <= 0; rx_irq_mask <= 0; host_error <= 0;
            phase <= 0; fetched_valid <= 0; pins_out <= 0; pins_oe <= 0;
            input_meta <= 0; input_sync <= 0;
        end else begin
            input_meta <= pins_in; input_sync <= input_meta;
            phase <= phase + 1'b1;
            if (phase == 0) fetched_valid <= running;
            if (host_tx && !tx_ready) host_error <= 1;
            if (write_enable) begin
                if (program_page) begin
                    if (!legal_program_write) host_error <= 1;
                    else if ({1'b0,address[3:0]} == program_length)
                        program_length <= program_length + 1'b1;
                end else case (address)
                    8'h03: if (write_data <= 1 && !memory_busy) running <= write_data[0] && !fault;
                        else host_error <= 1;
                    8'h04: if (write_data == 1) begin
                        running <= 0; fault <= 0; irq_pending <= 0; pc <= 0;
                        accumulator <= 0; delay_slots <= 0; counter <= 0; event_flag <= 0;
                    end else if (write_data != 0) host_error <= 1;
                    8'h05: if (write_data <= 1) irq_pending <= irq_pending && !write_data[0];
                        else host_error <= 1;
                    8'h06: if (write_data == 1) host_error <= 0; else host_error <= 1;
                    8'h0a: if (!running && !memory_busy && write_data == 0) begin
                        program_length <= 0; pc <= 0;
                    end else host_error <= 1;
                    8'h0c: if (write_data <= 1) rx_irq_mask <= write_data[0]; else host_error <= 1;
                    8'h0d: if (write_data <= 1) event_flag <= event_flag | write_data[0]; else host_error <= 1;
                    8'h0e: if (write_data <= 1) event_flag <= event_flag & ~write_data[0]; else host_error <= 1;
                    8'h10: if (!running && write_data[15:14] == 0 && (write_data[13:0] & reserved_pins) == 0) begin
                        output_mask <= write_data[13:0];
                        pins_out <= pins_out & ~output_mask;
                        pins_oe <= pins_oe & ~output_mask[7:0];
                    end else host_error <= 1;
                    8'h11: if (!running && write_data < 16) pc <= write_data[4:0]; else host_error <= 1;
                    8'h12: if (!running) accumulator <= write_data[7:0]; else host_error <= 1;
                    8'h14: begin end
                    8'h17: if (!running) counter <= write_data[3:0]; else host_error <= 1;
                    default: host_error <= 1;
                endcase
            end
            if (slot) begin
                if (delay_slots != 0) delay_slots <= delay_slots - 1'b1;
                else if (pc >= program_length) begin fault <= 1; running <= 0; end
                else begin
                    pc <= pc + 1'b1;
                    case (instruction[15:12])
                        4'h0: begin end
                        4'h1: accumulator <= instruction[7:0];
                        4'h2: accumulator <= instruction[8] ? {3'b0,input_sync[12:8]} : input_sync[7:0];
                        // OUT/OUT 1 retain seven-bit groups, now both owned by
                        // the single context. DIR controls all eight uio pins.
                        4'h3: if (instruction[8]) pins_out[13:7] <=
                            (pins_out[13:7] & ~output_mask[13:7]) | (accumulator[6:0] & output_mask[13:7]);
                            else pins_out[6:0] <= (pins_out[6:0] & ~output_mask[6:0]) | (accumulator[6:0] & output_mask[6:0]);
                        4'h4: pins_oe <= (pins_oe & ~output_mask[7:0]) | (accumulator & output_mask[7:0]);
                        4'h5, 4'h6: if (instruction[11:4] != 0) begin fault <= 1; running <= 0; end
                            else if (instruction[15:12] == 5 || accumulator != 0) pc <= {1'b0,instruction[3:0]};
                        4'h7: accumulator <= accumulator - 1'b1;
                        4'h8: if (instruction[3:0] > 12) begin fault <= 1; running <= 0; end
                            else if (input_sync[instruction[3:0]] != instruction[8]) pc <= pc;
                        4'h9: delay_slots <= instruction[7:0];
                        4'ha: accumulator <= accumulator ^ instruction[7:0];
                        4'hb: accumulator <= {accumulator[6:0],1'b0};
                        4'hc: accumulator <= {1'b0,accumulator[7:1]};
                        4'hd: irq_pending <= 1;
                        4'he: running <= 0;
                        4'hf: casez (instruction)
                            16'hf000: if (pull) accumulator <= tx_q; else pc <= pc;
                            16'hf100: if (!push) pc <= pc;
                            16'b1111_0010_????_000?, 16'b1111_0011_????_0000: begin
                                if (instruction[7:4] > 13) begin fault <= 1; running <= 0; end
                                else begin
                                    for (p = 0; p < 14; p = p + 1)
                                        if (instruction[7:4] == p[3:0] && output_mask[p])
                                            pins_out[p] <= instruction[8] ? accumulator[7] : instruction[0];
                                    if (instruction[8]) accumulator <= {accumulator[6:0],1'b0};
                                end
                            end
                            16'b1111_0100_0000_????: if (instruction[3:0] > 12) begin fault <= 1; running <= 0; end
                                else accumulator <= {accumulator[6:0],input_sync[instruction[3:0]]};
                            16'b1111_0101_0000_????: counter <= instruction[3:0];
                            16'b1111_0110_0000_????: begin
                                counter <= counter - 1'b1;
                                if (counter != 1) pc <= {1'b0,instruction[3:0]};
                            end
                            16'hf710: if (event_flag) event_flag <= 0; else pc <= pc;
                            16'hf720: event_flag <= 0;
                            16'b1111_1000_0000_????: if (accumulator[7]) pc <= {1'b0,instruction[3:0]};
                            default: begin fault <= 1; running <= 0; end
                        endcase
                    endcase
                end
            end
        end
    end
endmodule

