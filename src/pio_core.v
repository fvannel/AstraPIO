// SPDX-License-Identifier: Apache-2.0
`default_nettype none

// Two interleaved contexts, 256-byte synchronous instruction SRAM.
// Fetch low, fetch high, execute/data for each context: six clocks/context.
module pio_core (
    input wire clk, rst_n,
    input wire [7:0] address,
    input wire [15:0] write_data,
    input wire write_enable,
    input wire read_commit, read_busy,
    output wire read_valid,
    output reg [15:0] read_data,
    input wire [12:0] pins_in,
    output reg [13:0] pins_out,
    output reg [7:0] pins_oe,
    output wire irq
);
    reg [5:0] program_length [0:1];
    reg [7:0] memory_pointer;
    reg [5:0] pc [0:1];
    reg [7:0] accumulator [0:1];
    reg [7:0] delay_slots [0:1];
    reg [3:0] counter [0:1];
    reg [6:0] output_mask [0:1];
    wire [13:0] ownership [0:1];
    assign ownership[0] = {7'b0, output_mask[0]};
    assign ownership[1] = {output_mask[1], 7'b0};
    reg [1:0] running, faults, irq_pending;
    reg [1:0] events, rx_irq_mask;
    reg host_error;
    reg [2:0] phase;
    reg fetched_valid;
    wire turn = phase >= 3;
    // One datapath services both contexts; only architectural state is duplicated.
    wire [7:0] active_accumulator = accumulator[turn];
    wire [7:0] active_delay = delay_slots[turn];
    wire [5:0] active_pc = pc[turn];
    wire [3:0] active_counter = counter[turn];
    wire fetch_low = phase == 0 || phase == 3;
    wire fetch_high = phase == 1 || phase == 4;
    wire data_slot = phase == 2 || phase == 5;
    reg [7:0] low_byte;
    reg [15:0] program_read_word;
    reg program_pending, program_high;
    wire [7:0] ram_q;
    (* async_reg = "true" *) reg [12:0] input_meta, input_sync;
    wire [15:0] instruction = {ram_q, low_byte};
    wire selected_context = address[5];
    wire context_page = (address[7:4] == 4'h1 || address[7:4] == 4'h2);
    wire program_page = address[7:5] == 3'b010;
    wire memory_access = program_page || address == 8'h0b;
    // Keep the first 16 words of both contexts accessible via v0 aliases.
    wire [7:0] host_memory_address = program_page ?
        {1'b0, address[4], 2'b00, address[3:0]} : memory_pointer;
    wire legal_program_write = running == 0 && !host_memory_address[7] &&
        host_memory_address[5:0] < 48 &&
        host_memory_address[5:0] <= program_length[host_memory_address[6]];
    wire memory_write = write_enable && memory_access && legal_program_write;
    wire [6:0] code_address = (running != 0) ?
        {turn, pc[turn]} : host_memory_address[6:0];
    wire control_this_slot = write_enable && (
        address == 8'h03 || (address == 8'h04 && write_data[{3'b0, turn}]));
    wire executing = data_slot && fetched_valid && running[turn] &&
        !control_this_slot && delay_slots[turn] == 0 &&
        pc[turn] < program_length[turn];
    wire [7:0] stream_address, stream_data, pull_data;
    wire stream_write, stream_overflow, pull_accept, push_accept, recv_accept;
    wire pull_return, pull_context;
    wire [15:0] rx_data;
    wire [15:0] fifo_status;
    wire [1:0] rx_available;
    wire [1:0] rx_valid;
    wire fifo_read = context_page && address[3:0] == 4'h5;
    assign read_valid = !fifo_read || rx_valid[selected_context];
    wire [1:0] flush = write_enable && address == 8'h04 ? write_data[1:0] : 2'b0;
    pio_stream streams (
        .clk(clk), .rst_n(rst_n), .slot(data_slot), .flush(flush),
        .host_context(selected_context),
        .host_tx_write(write_enable && context_page && address[3:0] == 4'h4),
        .host_rx_pop(read_commit && fifo_read), .host_rx_lock(read_busy && fifo_read),
        .host_data(write_data[7:0]), .exec_context(turn),
        .exec_pull(executing && instruction == 16'hf000),
        .exec_push(executing && instruction == 16'hf100),
        .exec_recv(executing && instruction == 16'hf900),
        .exec_data(accumulator[turn][7:0]),
        .pull_accept(pull_accept), .push_accept(push_accept), .recv_accept(recv_accept),
        .pull_return(pull_return), .pull_context(pull_context),
        .pull_data(pull_data), .overflow(stream_overflow),
        .rx_valid(rx_valid), .host_rx_data(rx_data), .host_status(fifo_status), .rx_available(rx_available),
        .ram_address(stream_address), .ram_data(stream_data), .ram_write(stream_write), .ram_q(ram_q)
    );
    integer i, p;

    pio_sram imem (
        .clk(clk), .rst_n(rst_n),
        .write_enable(data_slot ? stream_write : (fetch_low ? program_pending : program_high)),
        .address(data_slot ? stream_address : {code_address, fetch_high}),
        .data_in(data_slot ? stream_data : (fetch_high ? write_data[15:8] : write_data[7:0])),
        .data_out(ram_q)
    );
    always @(posedge clk) begin
        if (fetch_high) low_byte <= ram_q;
        if (data_slot) program_read_word <= instruction;
    end

    assign irq = |irq_pending | |faults | host_error |
        (|(rx_available & rx_irq_mask));

    always @* begin
        read_data = 0;
        if (memory_access) begin
            if (running == 0 && !host_memory_address[7] &&
                host_memory_address[5:0] < program_length[host_memory_address[6]])
                read_data = program_read_word;
        end else if (context_page) begin
            case (address[3:0])
                4'h0: read_data = {2'b0, ownership[selected_context]};
                4'h1: read_data = {10'b0, pc[selected_context]};
                4'h2: read_data = {8'b0, accumulator[selected_context]};
                4'h3: read_data = {8'b0, delay_slots[selected_context]};
                4'h5: read_data = {rx_valid[selected_context], 7'b0,
                                  selected_context ? rx_data[15:8] : rx_data[7:0]};
                4'h6: read_data = fifo_status;
                4'h7: read_data = {12'b0, counter[selected_context]};
                4'hf: read_data = {10'b0, program_length[selected_context]};
                default: read_data = 0;
            endcase
        end else begin
            case (address)
                8'h00: read_data = 16'h5049; // PI
                8'h01: read_data = 16'h0200; // Byte-oriented ISA/ABI v2
                8'h02, 8'h03: read_data = {14'b0, running};
                8'h05: read_data = {14'b0, irq_pending};
                8'h06: read_data = {6'b0, faults, 7'b0, host_error};
                8'h07: read_data = {2'b0, pins_out};
                8'h08: read_data = {8'b0, pins_oe};
                8'h09: read_data = {3'b0, input_sync};
                8'h0a: read_data = {8'b0, memory_pointer};
                8'h0c: read_data = {14'b0, rx_irq_mask};
                8'h0d, 8'h0e: read_data = {14'b0, events};
                default: read_data = 0;
            endcase
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            memory_pointer <= 0;
            running <= 0;
            faults <= 0;
            irq_pending <= 0;
            events <= 0;
            rx_irq_mask <= 0;
            host_error <= 0;
            phase <= 0;
            fetched_valid <= 0;
            program_pending <= 0;
            program_high <= 0;
            pins_out <= 0;
            pins_oe <= 0;
            input_meta <= 0;
            input_sync <= 0;
            for (i = 0; i < 2; i = i + 1) begin
                pc[i] <= 0;
                program_length[i] <= 0;
                accumulator[i] <= 0;
                delay_slots[i] <= 0;
                counter[i] <= 0;
                output_mask[i] <= 0;
            end
        end else begin
            input_meta <= pins_in;
            input_sync <= input_meta;
            phase <= phase == 5 ? 3'b0 : phase + 1'b1;
            if (fetch_low) fetched_valid <= running[turn];
            if (fetch_low && program_pending) begin
                program_pending <= 0;
                program_high <= 1;
            end
            if (fetch_high) program_high <= 0;
            if (memory_write) program_pending <= 1;
            if (stream_overflow) host_error <= 1;
            for (i = 0; i < 2; i = i + 1)
                if (pull_return && pull_context == (i != 0)) accumulator[i] <= pull_data;

            // Host control does not steal execution slots, except explicit
            // RUN/RESTART commands. Only stopped contexts may be reconfigured.
            if (write_enable) begin
                if (memory_access) begin
                    if (legal_program_write) begin
                        // Append sequentially or overwrite an initialized word.
                        // Reject holes so reset cannot expose uninitialized code.
                        for (i = 0; i < 2; i = i + 1)
                            if (host_memory_address[6] == (i != 0) &&
                                host_memory_address[5:0] == program_length[i])
                                program_length[i] <= program_length[i] + 1'b1;
                    end else host_error <= 1;
                end else if (context_page) begin
                    case (address[3:0])
                        4'h0: begin
                            if (running == 0 && (selected_context ?
                                ((write_data & 16'hc07f) == 0) : ((write_data & 16'hff80) == 0))) begin
                                for (i = 0; i < 2; i = i + 1)
                                    if (selected_context == (i != 0))
                                        output_mask[i] <= selected_context ? write_data[13:7] : write_data[6:0];
                                pins_out <= pins_out & ~ownership[selected_context];
                                pins_oe <= pins_oe & ~ownership[selected_context][7:0];
                            end else host_error <= 1;
                        end
                        4'h1: begin
                            if (!running[selected_context]) begin
                                for (i = 0; i < 2; i = i + 1)
                                    if (selected_context == (i != 0)) pc[i] <= write_data[5:0];
                            end
                            else host_error <= 1;
                        end
                        4'h2: begin
                            if (!running[selected_context]) begin
                                for (i = 0; i < 2; i = i + 1)
                                    if (selected_context == (i != 0)) accumulator[i] <= write_data[7:0];
                            end
                            else host_error <= 1;
                        end
                        4'h4: begin end // Queue controller commits or reports overflow.
                        4'h7: begin
                            if (!running[selected_context]) begin
                                for (i = 0; i < 2; i = i + 1)
                                    if (selected_context == (i != 0)) counter[i] <= write_data[3:0];
                            end else host_error <= 1;
                        end
                        4'hf: begin
                            if (running == 0 && write_data == 0) begin
                                for (i = 0; i < 2; i = i + 1)
                                    if (selected_context == (i != 0)) begin
                                        program_length[i] <= 0;
                                        pc[i] <= 0;
                                    end
                            end else host_error <= 1;
                        end
                        default: host_error <= 1;
                    endcase
                end else begin
                    case (address)
                        8'h03: running <= write_data[1:0] & ~faults;
                        8'h04: begin
                            for (i = 0; i < 2; i = i + 1) begin
                                if (write_data[i]) begin
                                    running[i] <= 0;
                                    faults[i] <= 0;
                                    irq_pending[i] <= 0;
                                    pc[i] <= 0;
                                    accumulator[i] <= 0;
                                    delay_slots[i] <= 0;
                                    counter[i] <= 0;
                                    events[i] <= 0;
                                end
                            end
                            // RESTART retains GPIO levels/directions. Releasing
                            // ownership while stopped clears those pins.
                        end
                        8'h05: irq_pending <= irq_pending & ~write_data[1:0];
                        8'h06: if (write_data[0]) host_error <= 0;
                        8'h0a: memory_pointer <= write_data[7:0];
                        8'h0c: rx_irq_mask <= write_data[1:0];
                        8'h0d: events <= events | write_data[1:0];
                        8'h0e: events <= events & ~write_data[1:0];
                        default: host_error <= 1;
                    endcase
                end
            end

            for (i = 0; i < 2; i = i + 1) begin
              if (data_slot && turn == (i != 0) && fetched_valid && running[turn] && !control_this_slot) begin
                if (active_delay != 0)
                    delay_slots[i] <= active_delay - 1'b1;
                else if (active_pc >= program_length[turn]) begin
                    faults[i] <= 1;
                    running[i] <= 0;
                end else begin
                    pc[i] <= active_pc + 1'b1;
                    case (instruction[15:12])
                        4'h0: begin end // NOP
                        4'h1: accumulator[i] <= instruction[7:0]; // LDI byte
                        4'h2: accumulator[i] <= instruction[8] ? {3'b0, input_sync[12:8]} : input_sync[7:0]; // IN bank
                        4'h3: pins_out <= (pins_out & ~ownership[i]) |
                                         ((i == 0 ? {7'b0, accumulator[i][6:0]} :
                                                    {accumulator[i][6:0], 7'b0}) & ownership[i]); // OUT bank
                        4'h4: pins_oe <= (pins_oe & ~ownership[i][7:0]) |
                                        ((i == 0 ? {1'b0, accumulator[i][6:0]} :
                                                   {accumulator[i][0], 7'b0}) & ownership[i][7:0]); // DIR bank
                        4'h5: pc[i] <= instruction[5:0]; // JMP
                        4'h6: if (active_accumulator != 0) pc[i] <= instruction[5:0]; // JNZ
                        4'h7: accumulator[i] <= active_accumulator - 1'b1; // DEC
                        4'h8: begin // WAIT input index, level
                            if (instruction[3:0] > 12) begin
                                faults[i] <= 1;
                                running[i] <= 0;
                            end else if (input_sync[instruction[3:0]] != instruction[8])
                                pc[i] <= pc[i];
                        end
                        4'h9: delay_slots[i] <= instruction[7:0]; // DELAY
                        4'ha: accumulator[i] <= active_accumulator ^ instruction[7:0];
                        4'hb: accumulator[i] <= {active_accumulator[6:0], 1'b0}; // SHL
                        4'hc: accumulator[i] <= {1'b0, active_accumulator[7:1]}; // SHR
                        4'hd: irq_pending[i] <= 1; // IRQ
                        4'he: running[i] <= 0; // HALT
                        4'hf: begin
                            casez (instruction)
                                16'hf000: begin // PULL byte, blocking
                                    if (!pull_accept) pc[i] <= pc[i];
                                end
                                16'hf100: if (!push_accept) pc[i] <= pc[i]; // PUSH byte
                                16'b1111_0010_0???_000?, // SET local output, constant level
                                16'b1111_0011_0???_0000: begin // OUTBIT local pin, MSB then shift
                                    if (instruction[6:4] > 6) begin
                                        faults[i] <= 1;
                                        running[i] <= 0;
                                    end else begin
                                        for (p = 0; p < 7; p = p + 1)
                                            if (instruction[6:4] == p[2:0] && output_mask[i][p])
                                                pins_out[i * 7 + p] <= instruction[8] ? accumulator[i][7] : instruction[0];
                                        if (instruction[8]) accumulator[i] <= {active_accumulator[6:0], 1'b0};
                                    end
                                end
                                16'b1111_0100_0000_????: begin // INBIT global input index
                                    if (instruction[3:0] > 12) begin
                                        faults[i] <= 1;
                                        running[i] <= 0;
                                    end else accumulator[i] <= {active_accumulator[6:0], input_sync[instruction[3:0]]};
                                end
                                16'b1111_0101_0000_????: counter[i] <= instruction[3:0]; // LDX
                                16'b1111_0110_00??_????: begin // DJNZ (0 means 16 iterations)
                                    counter[i] <= active_counter - 1'b1;
                                    if (active_counter != 1) pc[i] <= instruction[5:0];
                                end
                                16'hf700: events[1-i] <= 1; // SIGNAL peer
                                16'hf710: begin // AWAIT and consume own event
                                    if (events[i]) events[i] <= 0;
                                    else pc[i] <= pc[i];
                                end
                                16'hf720: events[i] <= 0; // CLR_EVENT
                                16'b1111_1000_00??_????: // JBIT on accumulator MSB
                                    if (active_accumulator[7]) pc[i] <= instruction[5:0];
                                16'hf900: begin // RECV peer's RX queue (host consumption is exclusive).
                                    if (!recv_accept) pc[i] <= pc[i];
                                end
                                default: begin faults[i] <= 1; running[i] <= 0; end
                            endcase
                        end
                        default: begin faults[i] <= 1; running[i] <= 0; end
                    endcase
                end
              end
            end
        end
    end
endmodule
