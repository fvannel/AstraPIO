// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// ABI v6 OUTMSB-only candidate: one context, 16 native ten-bit words, two-byte TX and RX queues.
// Preserve the v3 4-clock instruction cadence: fetch, execute, idle, idle.
module pio_single_core (
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
    reg [9:0] instruction;
    (* async_reg = "true" *) reg [12:0] input_meta, input_sync;
    assign sampled_inputs = input_sync;
    assign claimed_pins = output_mask;
    wire memory_busy;
    wire [9:0] program_q;
    wire program_page = address[7:4] == 4'h4;
    wire legal_program_write = !running && !memory_busy && write_data[15:10] == 0 &&
        {1'b0,address[3:0]} <= program_length;
    wire restart = write_enable && address == 4 && write_data == 1;
    wire host_run = write_enable && address == 3 && write_data <= 1;
    wire control_this_slot = restart || host_run;
    wire slot = phase == 1 && fetched_valid && running && !control_this_slot;
    wire executing = slot && delay_slots == 0 && pc < program_length;
    pio_program #(.WIDTH(10)) imem (
        .clk(clk), .rst_n(rst_n),
        .write_enable(write_enable && program_page && legal_program_write),
        .write_address(address[3:0]), .write_data(write_data[9:0]),
        .read_address(running ? pc[3:0] : address[3:0]),
        .read_data(program_q), .busy(memory_busy)
    );
    always @(posedge clk) if (phase == 0) instruction <= program_q;
    wire tx_empty, tx_full, tx_ready, rx_empty, rx_full, rx_ready;
    wire [7:0] tx_q, rx_q;
    wire [1:0] tx_level, rx_level;
    wire host_tx = write_enable && address == 8'h14;
    wire pull = executing && instruction == 10'h307 && !tx_empty && !restart;
    wire push = executing && instruction == 10'h308 && rx_ready && !restart;
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
                read_data = {6'b0,program_q};
        end else case (address)
            8'h00: read_data = 16'h5049;
            8'h01: read_data = 16'h0600;
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
            8'h1a: read_data = 16'h0004; // OUTMSB is the sole extension.
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
                    // 00/01/10 carry an eight-bit literal. 11 selects a
                    // four-bit operation plus four-bit pin/address/function.
                    // Decode natively: no expanded 16-bit instruction register.
                    case (instruction[9:8])
                        2'b00: accumulator <= instruction[7:0];
                        2'b01: delay_slots <= instruction[7:0];
                        2'b10: accumulator <= accumulator ^ instruction[7:0];
                        2'b11: case (instruction[7:4])
                            4'h0: case (instruction[3:0])
                                4'h0: begin end
                                4'h1: pins_oe <= (pins_oe & ~output_mask[7:0]) | (accumulator & output_mask[7:0]);
                                4'h2: accumulator <= accumulator - 1'b1;
                                4'h3: accumulator <= {accumulator[6:0],1'b0};
                                4'h4: accumulator <= {1'b0,accumulator[7:1]};
                                4'h5: irq_pending <= 1;
                                4'h6: running <= 0;
                                4'h7: if (pull) accumulator <= tx_q; else pc <= pc;
                                4'h8: if (!push) pc <= pc;
                                4'h9: if (event_flag) event_flag <= 0; else pc <= pc;
                                4'ha: event_flag <= 0;
                                4'hb: accumulator <= input_sync[7:0];
                                4'hc: accumulator <= {3'b0,input_sync[12:8]};
                                4'hd: pins_out[6:0] <= (pins_out[6:0] & ~output_mask[6:0]) | (accumulator[6:0] & output_mask[6:0]);
                                4'he: pins_out[13:7] <= (pins_out[13:7] & ~output_mask[13:7]) | (accumulator[6:0] & output_mask[13:7]);
                                default: begin fault <= 1; running <= 0; end
                            endcase
                            4'h1, 4'h2, 4'h3: if (instruction[7:4] == 1 ||
                                (instruction[7:4] == 2 && accumulator != 0) ||
                                (instruction[7:4] == 3 && accumulator[7])) pc <= {1'b0,instruction[3:0]};
                            4'h4, 4'h5: if (instruction[3:0] > 12) begin fault <= 1; running <= 0; end
                                else if (input_sync[instruction[3:0]] != instruction[4]) pc <= pc;
                            4'h6, 4'h7, 4'h8: begin
                                if (instruction[3:0] > 13) begin fault <= 1; running <= 0; end
                                else begin
                                    for (p = 0; p < 14; p = p + 1)
                                        if (instruction[3:0] == p[3:0] && output_mask[p])
                                            pins_out[p] <= instruction[7] ? accumulator[7] : instruction[4];
                                    if (instruction[7]) accumulator <= {accumulator[6:0],1'b0};
                                end
                            end
                            4'h9: if (instruction[3:0] > 12) begin fault <= 1; running <= 0; end
                                else accumulator <= {accumulator[6:0],input_sync[instruction[3:0]]};
                            4'ha: counter <= instruction[3:0];
                            4'hb: begin
                                counter <= counter - 1'b1;
                                if (counter != 1) pc <= {1'b0,instruction[3:0]};
                            end
                            4'he: begin
                                if (instruction[3:0] > 13) begin fault <= 1; running <= 0; end
                                else if (output_mask[instruction[3:0]]) pins_out[instruction[3:0]] <= accumulator[7];
                            end
                            default: begin fault <= 1; running <= 0; end
                        endcase
                    endcase
                end
            end
        end
    end
endmodule
