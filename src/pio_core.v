// SPDX-License-Identifier: Apache-2.0
`default_nettype none

// ISA v0: two fixed round-robin contexts, 16 x 16-bit instructions each.
// No protocol-specific logic. Program storage is inferred logic, NOT a SRAM macro.
module pio_core (
    input wire clk, rst_n,
    input wire [7:0] address,
    input wire [15:0] write_data,
    input wire write_enable,
    output reg [15:0] read_data,
    input wire [12:0] pins_in,
    output reg [13:0] pins_out,
    output reg [7:0] pins_oe,
    output wire irq
);
    reg [15:0] program_mem [0:31];
    reg [31:0] program_valid;
    reg [3:0] pc [0:1];
    reg [15:0] accumulator [0:1];
    reg [11:0] delay_slots [0:1];
    reg [13:0] ownership [0:1];
    reg [1:0] running, faults, irq_pending;
    reg host_error;
    reg turn;
    (* async_reg = "true" *) reg [12:0] input_meta, input_sync;
    wire [4:0] fetch_address = {turn, pc[turn]};
    wire [15:0] instruction = program_mem[fetch_address];
    wire selected_context = address[5];
    wire context_page = (address[7:4] == 4'h1 || address[7:4] == 4'h2);
    wire program_page = address[7:5] == 3'b010;
    wire control_this_slot = write_enable && (
        address == 8'h03 || (address == 8'h04 && write_data[turn]));
    integer i;

    assign irq = |irq_pending | |faults | host_error;

    always @* begin
        read_data = 0;
        if (program_page) begin
            if (program_valid[address[4:0]])
                read_data = program_mem[address[4:0]];
        end else if (context_page) begin
            case (address[3:0])
                4'h0: read_data = {2'b0, ownership[selected_context]};
                4'h1: read_data = {12'b0, pc[selected_context]};
                4'h2: read_data = accumulator[selected_context];
                4'h3: read_data = {4'b0, delay_slots[selected_context]};
                default: read_data = 0;
            endcase
        end else begin
            case (address)
                8'h00: read_data = 16'h5049; // PI
                8'h01: read_data = 16'h0001; // ABI v0, revision 1
                8'h02, 8'h03: read_data = {14'b0, running};
                8'h05: read_data = {14'b0, irq_pending};
                8'h06: read_data = {6'b0, faults, 7'b0, host_error};
                8'h07: read_data = {2'b0, pins_out};
                8'h08: read_data = {8'b0, pins_oe};
                8'h09: read_data = {3'b0, input_sync};
                default: read_data = 0;
            endcase
        end
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            program_valid <= 0;
            running <= 0;
            faults <= 0;
            irq_pending <= 0;
            host_error <= 0;
            turn <= 0;
            pins_out <= 0;
            pins_oe <= 0;
            input_meta <= 0;
            input_sync <= 0;
            for (i = 0; i < 2; i = i + 1) begin
                pc[i] <= 0;
                accumulator[i] <= 0;
                delay_slots[i] <= 0;
                ownership[i] <= 0;
            end
        end else begin
            input_meta <= pins_in;
            input_sync <= input_meta;
            turn <= ~turn;

            // Host control does not steal execution slots, except explicit
            // RUN/RESTART commands. Only stopped contexts may be reconfigured.
            if (write_enable) begin
                if (program_page) begin
                    if (running == 0) begin
                        program_mem[address[4:0]] <= write_data;
                        program_valid[address[4:0]] <= 1;
                    end else host_error <= 1;
                end else if (context_page) begin
                    case (address[3:0])
                        4'h0: begin
                            if (running == 0 &&
                                (write_data[13:0] & ownership[!selected_context]) == 0) begin
                                ownership[selected_context] <= write_data[13:0];
                                pins_out <= pins_out & ~ownership[selected_context];
                                pins_oe <= pins_oe & ~ownership[selected_context][7:0];
                            end else host_error <= 1;
                        end
                        4'h1: begin
                            if (!running[selected_context]) pc[selected_context] <= write_data[3:0];
                            else host_error <= 1;
                        end
                        4'h2: begin
                            if (!running[selected_context]) accumulator[selected_context] <= write_data;
                            else host_error <= 1;
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
                                end
                            end
                            // RESTART retains GPIO levels/directions. Releasing
                            // ownership while stopped clears those pins.
                        end
                        8'h05: irq_pending <= irq_pending & ~write_data[1:0];
                        8'h06: if (write_data[0]) host_error <= 0;
                        default: host_error <= 1;
                    endcase
                end
            end

            if (running[turn] && !control_this_slot) begin
                if (delay_slots[turn] != 0)
                    delay_slots[turn] <= delay_slots[turn] - 1'b1;
                else if (!program_valid[fetch_address]) begin
                    faults[turn] <= 1;
                    running[turn] <= 0;
                end else begin
                    pc[turn] <= pc[turn] + 1'b1;
                    case (instruction[15:12])
                        4'h0: begin end // NOP
                        4'h1: accumulator[turn] <= {4'b0, instruction[11:0]}; // LDI
                        4'h2: accumulator[turn] <= {3'b0, input_sync}; // IN
                        4'h3: pins_out <= (pins_out & ~ownership[turn]) |
                                         (accumulator[turn][13:0] & ownership[turn]); // OUT
                        4'h4: pins_oe <= (pins_oe & ~ownership[turn][7:0]) |
                                        (accumulator[turn][7:0] & ownership[turn][7:0]); // DIR
                        4'h5: pc[turn] <= instruction[3:0]; // JMP
                        4'h6: if (accumulator[turn] != 0) pc[turn] <= instruction[3:0]; // JNZ
                        4'h7: accumulator[turn] <= accumulator[turn] - 1'b1; // DEC
                        4'h8: begin // WAIT input index, level
                            if (instruction[3:0] > 12) begin
                                faults[turn] <= 1;
                                running[turn] <= 0;
                            end else if (input_sync[instruction[3:0]] != instruction[8])
                                pc[turn] <= pc[turn];
                        end
                        4'h9: delay_slots[turn] <= instruction[11:0]; // DELAY
                        4'ha: accumulator[turn] <= accumulator[turn] ^ {4'b0, instruction[11:0]};
                        4'hb: accumulator[turn] <= {accumulator[turn][14:0], 1'b0}; // SHL
                        4'hc: accumulator[turn] <= {1'b0, accumulator[turn][15:1]}; // SHR
                        4'hd: irq_pending[turn] <= 1; // IRQ
                        4'he: running[turn] <= 0; // HALT
                        default: begin faults[turn] <= 1; running[turn] <= 0; end
                    endcase
                end
            end
        end
    end
endmodule
