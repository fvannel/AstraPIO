// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// Compact ABI v3: fetch0, execute0, fetch1, execute1; shared 16-word program.
module pio_core (
    input wire clk, rst_n,
    input wire [7:0] address,
    input wire [15:0] write_data,
    input wire write_enable, read_commit, read_busy,
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
    reg [4:0] program_length;
    reg [4:0] pc [0:1]; // fifth bit detects falling off word 15, never wraps.
    reg [7:0] accumulator [0:1], delay_slots [0:1];
    reg [3:0] counter [0:1];
    reg [6:0] output_mask [0:1];
    wire [13:0] ownership [0:1];
    assign ownership[0] = {7'b0, output_mask[0]};
    assign ownership[1] = {output_mask[1], 7'b0};
    reg [1:0] running, faults, irq_pending, events, rx_irq_mask;
    reg host_error;
    reg [1:0] phase;
    reg fetched_valid;
    reg [15:0] instruction;
    (* async_reg = "true" *) reg [12:0] input_meta, input_sync;
    assign sampled_inputs = input_sync;
    assign claimed_pins = ownership[0] | ownership[1];
    wire turn = phase[1];
    wire execute_slot = phase[0];
    wire context_page = address[7:4] == 4'h1 || address[7:4] == 4'h2;
    wire selected_context = address[5];
    wire program_page = address[7:4] == 4'h4;
    wire memory_busy;
    wire legal_program_write = running == 0 && !memory_busy &&
        {1'b0, address[3:0]} <= program_length;
    wire memory_write = write_enable && program_page && legal_program_write;
    wire [15:0] program_q;
    pio_program imem (
        .clk(clk), .rst_n(rst_n), .write_enable(memory_write),
        .write_address(address[3:0]), .write_data(write_data),
        .read_address(running != 0 ? pc[turn][3:0] : address[3:0]),
        .read_data(program_q), .busy(memory_busy)
    );
    always @(posedge clk) if (!execute_slot) instruction <= program_q;
    wire control_this_slot = write_enable && (address == 8'h03 ||
        (address == 8'h04 && write_data[{3'b0, turn}]));
    wire executing = execute_slot && fetched_valid && running[turn] &&
        !control_this_slot && delay_slots[turn] == 0 && pc[turn] < program_length;
    wire fifo_read = context_page && address[3:0] == 4'h5;
    wire [1:0] rx_available;
    wire [15:0] fifo_status;
    wire [7:0] host_rx_data, pull_data, peer_data;
    wire pull_accept, push_accept, recv_accept, overflow;
    wire [1:0] flush = write_enable && address == 8'h04 ? write_data[1:0] : 2'b0;
    assign read_valid = !fifo_read || rx_available[selected_context];
    pio_queues streams (
        .clk(clk), .rst_n(rst_n), .flush(flush), .host_context(selected_context),
        .host_tx_write(write_enable && context_page && address[3:0] == 4'h4),
        .host_rx_pop(read_commit && fifo_read), .host_rx_lock(read_busy && fifo_read),
        .host_data(write_data[7:0]), .exec_context(turn),
        .exec_pull(executing && instruction == 16'hf000),
        .exec_push(executing && instruction == 16'hf100),
        .exec_recv(executing && instruction == 16'hf900), .exec_data(accumulator[turn]),
        .pull_accept(pull_accept), .push_accept(push_accept), .recv_accept(recv_accept),
        .pull_data(pull_data), .peer_data(peer_data), .host_rx_data(host_rx_data),
        .rx_available(rx_available), .host_status(fifo_status), .overflow(overflow)
    );
    assign irq = |irq_pending | |faults | host_error | |(rx_available & rx_irq_mask);
    always @* begin
        read_data = 0;
        if (program_page) begin
            if (running == 0 && !memory_busy && {1'b0,address[3:0]} < program_length)
                read_data = program_q;
        end else if (context_page) begin
            case (address[3:0])
                4'h0: read_data = {2'b0, ownership[selected_context]};
                4'h1: read_data = {11'b0, pc[selected_context]};
                4'h2: read_data = {8'b0, accumulator[selected_context]};
                4'h3: read_data = {8'b0, delay_slots[selected_context]};
                4'h5: read_data = {rx_available[selected_context], 7'b0, host_rx_data};
                4'h6: read_data = fifo_status;
                4'h7: read_data = {12'b0, counter[selected_context]};
                4'hf: read_data = {11'b0, program_length};
                default: read_data = 0;
            endcase
        end else begin
            case (address)
                8'h00: read_data = 16'h5049;
                8'h01: read_data = 16'h0300;
                8'h02, 8'h03: read_data = {14'b0, running};
                8'h05: read_data = {14'b0, irq_pending};
                8'h06: read_data = {6'b0, faults, 7'b0, host_error};
                8'h07: read_data = {2'b0, pins_out};
                8'h08: read_data = {8'b0, pins_oe};
                8'h09: read_data = {3'b0, input_sync};
                8'h0a: read_data = {11'b0, program_length};
                8'h0b: read_data = {15'b0, memory_busy};
                8'h0c: read_data = {14'b0, rx_irq_mask};
                8'h0d, 8'h0e: read_data = {14'b0, events};
                8'h0f: read_data = 16'h1002;
                default: read_data = 0;
            endcase
        end
    end
    integer i, p;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            program_length <= 0;
            running <= 0; faults <= 0; irq_pending <= 0; events <= 0;
            rx_irq_mask <= 0; host_error <= 0; phase <= 0; fetched_valid <= 0;
            pins_out <= 0; pins_oe <= 0; input_meta <= 0; input_sync <= 0;
            for (i = 0; i < 2; i = i + 1) begin
                pc[i] <= 0; accumulator[i] <= 0; delay_slots[i] <= 0;
                counter[i] <= 0; output_mask[i] <= 0;
            end
        end else begin
            input_meta <= pins_in; input_sync <= input_meta;
            phase <= phase + 1'b1;
            if (!execute_slot) fetched_valid <= running[turn];
            if (overflow) host_error <= 1;
            if (write_enable) begin
                if (program_page) begin
                    if (!legal_program_write) host_error <= 1;
                    else if ({1'b0,address[3:0]} == program_length)
                        program_length <= program_length + 1'b1;
                end else if (context_page) begin
                    case (address[3:0])
                        4'h0: begin
                            if (running == 0 && (write_data[13:0] & reserved_pins) == 0 && (selected_context ?
                                ((write_data & 16'hc07f) == 0) : ((write_data & 16'hff80) == 0))) begin
                                output_mask[selected_context] <= selected_context ? write_data[13:7] : write_data[6:0];
                                pins_out <= pins_out & ~ownership[selected_context];
                                pins_oe <= pins_oe & ~ownership[selected_context][7:0];
                            end else host_error <= 1;
                        end
                        4'h1: if (!running[selected_context] && write_data < 16)
                            pc[selected_context] <= write_data[4:0]; else host_error <= 1;
                        4'h2: if (!running[selected_context]) accumulator[selected_context] <= write_data[7:0];
                            else host_error <= 1;
                        4'h4: begin end
                        4'h7: if (!running[selected_context]) counter[selected_context] <= write_data[3:0];
                            else host_error <= 1;
                        default: host_error <= 1;
                    endcase
                end else begin
                    case (address)
                        8'h03: if (!memory_busy) running <= write_data[1:0] & ~faults; else host_error <= 1;
                        8'h04: for (i = 0; i < 2; i = i + 1) if (write_data[i]) begin
                            running[i] <= 0; faults[i] <= 0; irq_pending[i] <= 0;
                            pc[i] <= 0; accumulator[i] <= 0; delay_slots[i] <= 0;
                            counter[i] <= 0; events[i] <= 0;
                        end
                        8'h05: irq_pending <= irq_pending & ~write_data[1:0];
                        8'h06: if (write_data[0]) host_error <= 0;
                        8'h0a: if (running == 0 && !memory_busy && write_data == 0) begin
                            program_length <= 0; pc[0] <= 0; pc[1] <= 0;
                        end else host_error <= 1;
                        8'h0c: rx_irq_mask <= write_data[1:0];
                        8'h0d: events <= events | write_data[1:0];
                        8'h0e: events <= events & ~write_data[1:0];
                        default: host_error <= 1;
                    endcase
                end
            end
            for (i = 0; i < 2; i = i + 1) begin
                if (execute_slot && turn == (i != 0) && fetched_valid && running[turn] && !control_this_slot) begin
                    if (delay_slots[turn] != 0) delay_slots[i] <= delay_slots[turn] - 1'b1;
                    else if (pc[turn] >= program_length) begin faults[i] <= 1; running[i] <= 0; end
                    else begin
                        pc[i] <= pc[turn] + 1'b1;
                        case (instruction[15:12])
                            4'h0: begin end
                            4'h1: accumulator[i] <= instruction[7:0];
                            4'h2: accumulator[i] <= instruction[8] ? {3'b0, input_sync[12:8]} : input_sync[7:0];
                            4'h3: pins_out <= (pins_out & ~ownership[i]) |
                                ((i == 0 ? {7'b0, accumulator[i][6:0]} : {accumulator[i][6:0],7'b0}) & ownership[i]);
                            4'h4: pins_oe <= (pins_oe & ~ownership[i][7:0]) |
                                ((i == 0 ? {1'b0, accumulator[i][6:0]} : {accumulator[i][0],7'b0}) & ownership[i][7:0]);
                            4'h5, 4'h6: begin
                                if (instruction[11:4] != 0) begin faults[i] <= 1; running[i] <= 0; end
                                else if (instruction[15:12] == 5 || accumulator[turn] != 0)
                                    pc[i] <= {1'b0,instruction[3:0]};
                            end
                            4'h7: accumulator[i] <= accumulator[turn] - 1'b1;
                            4'h8: if (instruction[3:0] > 12) begin faults[i] <= 1; running[i] <= 0; end
                                else if (input_sync[instruction[3:0]] != instruction[8]) pc[i] <= pc[turn];
                            4'h9: delay_slots[i] <= instruction[7:0];
                            4'ha: accumulator[i] <= accumulator[turn] ^ instruction[7:0];
                            4'hb: accumulator[i] <= {accumulator[turn][6:0],1'b0};
                            4'hc: accumulator[i] <= {1'b0,accumulator[turn][7:1]};
                            4'hd: irq_pending[i] <= 1;
                            4'he: running[i] <= 0;
                            4'hf: casez (instruction)
                                16'hf000: if (pull_accept) accumulator[i] <= pull_data; else pc[i] <= pc[turn];
                                16'hf100: if (!push_accept) pc[i] <= pc[turn];
                                16'b1111_0010_0???_000?, 16'b1111_0011_0???_0000: begin
                                    if (instruction[6:4] > 6) begin faults[i] <= 1; running[i] <= 0; end
                                    else begin
                                        for (p = 0; p < 7; p = p + 1)
                                            if (instruction[6:4] == p[2:0] && output_mask[i][p])
                                                pins_out[i*7+p] <= instruction[8] ? accumulator[turn][7] : instruction[0];
                                        if (instruction[8]) accumulator[i] <= {accumulator[turn][6:0],1'b0};
                                    end
                                end
                                16'b1111_0100_0000_????: if (instruction[3:0] > 12) begin
                                    faults[i] <= 1; running[i] <= 0;
                                end else accumulator[i] <= {accumulator[turn][6:0],input_sync[instruction[3:0]]};
                                16'b1111_0101_0000_????: counter[i] <= instruction[3:0];
                                16'b1111_0110_0000_????: begin
                                    counter[i] <= counter[turn] - 1'b1;
                                    if (counter[turn] != 1) pc[i] <= {1'b0,instruction[3:0]};
                                end
                                16'hf700: events[1-i] <= 1;
                                16'hf710: if (events[i]) events[i] <= 0; else pc[i] <= pc[turn];
                                16'hf720: events[i] <= 0;
                                16'b1111_1000_0000_????: if (accumulator[turn][7]) pc[i] <= {1'b0,instruction[3:0]};
                                16'hf900: if (recv_accept) accumulator[i] <= peer_data; else pc[i] <= pc[turn];
                                default: begin faults[i] <= 1; running[i] <= 0; end
                            endcase
                        endcase
                    end
                end
            end
        end
    end
endmodule
