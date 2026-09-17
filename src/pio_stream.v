// SPDX-License-Identifier: Apache-2.0
`default_nettype none

// Four 16-byte queues in the otherwise unused quarter of the program SRAM.
// A data slot occurs every three clocks. Host reads prefetch one snapshot;
// there are no replicated data flops and no speculative destructive reads.
// Arbitration: host read snapshot, host TX write, PIO PULL/PUSH/RECV.
// Queue stalls never change the scheduler's phase or another context's PC.
module pio_stream (
    input wire clk, rst_n, slot,
    input wire [1:0] flush,
    input wire host_context, host_tx_write, host_rx_pop, host_rx_lock,
    input wire [7:0] host_data,
    input wire exec_context, exec_pull, exec_push, exec_recv,
    input wire [7:0] exec_data,
    output wire pull_accept, push_accept, recv_accept,
    output wire pull_return, pull_context,
    output wire [7:0] pull_data,
    output reg overflow,
    output wire [1:0] rx_valid,
    output wire [15:0] host_rx_data,
    output wire [15:0] host_status,
    output wire [1:0] rx_available,
    output reg [7:0] ram_address, ram_data,
    output reg ram_write,
    input wire [7:0] ram_q
);
    // Extended pointers distinguish full from empty without four extra counters.
    reg [4:0] tx_rp [0:1], tx_wp [0:1], rx_rp [0:1], rx_wp [0:1];
    wire [1:0] tx_empty, rx_empty, tx_full, rx_full;
    wire [4:0] host_tx_level = tx_wp[host_context] - tx_rp[host_context];
    wire [4:0] host_rx_level = rx_wp[host_context] - rx_rp[host_context];
    reg host_pending, pending_context;
    reg read_seen, host_read_pending, host_snapshot_valid;
    reg [7:0] host_snapshot;
    reg [1:0] read_kind;
    reg read_context;
    wire host_request = host_pending || host_tx_write;
    wire host_target = host_pending ? pending_context : host_context;
    reg grant_host, grant_snapshot, grant_pull, grant_push, grant_recv;
    wire [1:0] host_pop;
    wire [1:0] peer_pop;
    wire [1:0] rx_pop;
    assign rx_valid = host_snapshot_valid ? (host_context ? 2'b10 : 2'b01) : 2'b0;
    assign host_rx_data = {2{host_snapshot_valid ? host_snapshot : 8'b0}};
    assign host_status = {3'b0, host_rx_level, 3'b0, host_tx_level};
    assign rx_available = ~rx_empty;
    assign host_pop = host_rx_pop ? (host_context ? 2'b10 : 2'b01) : 2'b00;
    assign recv_accept = grant_recv;
    assign peer_pop = recv_accept ? (exec_context ? 2'b01 : 2'b10) : 2'b00;
    assign rx_pop = host_pop | peer_pop;
    assign pull_accept = grant_pull;
    assign push_accept = grant_push;
    assign pull_return = (read_kind == 1 || read_kind == 2) && !flush[read_context];
    assign pull_context = read_context;
    assign pull_data = ram_q;

    always @* begin
        grant_host = 0;
        grant_snapshot = 0;
        grant_pull = 0;
        grant_push = 0;
        grant_recv = 0;
        ram_address = 0;
        ram_data = 0;
        ram_write = 0;
        if (slot) begin
            if ((host_read_pending || (host_rx_lock && !read_seen)) && !flush[host_context]) begin
                grant_snapshot = 1;
                ram_address = {host_context, 3'b111, rx_rp[host_context][3:0]};
            end else if (host_request && !flush[host_target]) begin
                grant_host = 1;
                ram_address = {host_target, 3'b110, tx_wp[host_target][3:0]};
                ram_data = host_data;
                ram_write = !tx_full[host_target];
            end else if (exec_pull && !tx_empty[exec_context]) begin
                grant_pull = 1;
                ram_address = {exec_context, 3'b110, tx_rp[exec_context][3:0]};
            end else if (exec_push && (!rx_full[exec_context] || host_pop[exec_context])) begin
                grant_push = 1;
                ram_address = {exec_context, 3'b111, rx_wp[exec_context][3:0]};
                ram_data = exec_data;
                ram_write = 1;
            end else if (exec_recv && !rx_empty[!exec_context] &&
                         !(host_rx_lock && host_context != exec_context) &&
                         !host_pop[!exec_context] && !flush[!exec_context]) begin
                grant_recv = 1;
                ram_address = {!exec_context, 3'b111, rx_rp[!exec_context][3:0]};
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            host_pending <= 0;
            pending_context <= 0;
            read_kind <= 0;
            read_context <= 0;
            overflow <= 0;
            read_seen <= 0;
            host_read_pending <= 0;
            host_snapshot_valid <= 0;
            host_snapshot <= 0;
        end else begin
            overflow <= 0;
            read_kind <= 0;
            if (!host_rx_lock) read_seen <= 0;
            if (host_rx_lock && !read_seen) begin
                read_seen <= 1;
                host_read_pending <= 1;
                host_snapshot_valid <= 0;
            end
            if (host_tx_write) begin
                host_pending <= 1;
                pending_context <= host_context;
            end
            if (grant_host) begin
                host_pending <= 0;
                if (tx_full[host_target]) overflow <= 1;
            end
            if (flush[pending_context] && host_pending) host_pending <= 0;
            if (grant_pull || grant_recv) begin
                read_kind <= grant_pull ? 1 : 2;
                read_context <= exec_context;
            end
            if (grant_snapshot) begin
                host_read_pending <= 0;
                if (!rx_empty[host_context]) read_kind <= 3;
            end
            if (read_kind == 3) begin
                host_snapshot <= ram_q;
                host_snapshot_valid <= 1;
            end
        end
    end

    genvar c;
    generate for (c = 0; c < 2; c = c + 1) begin : queue_state
        assign tx_empty[c] = tx_wp[c] == tx_rp[c];
        assign rx_empty[c] = rx_wp[c] == rx_rp[c];
        assign tx_full[c] = tx_wp[c] == (tx_rp[c] ^ 5'b10000);
        assign rx_full[c] = rx_wp[c] == (rx_rp[c] ^ 5'b10000);
        wire tx_put = grant_host && host_target == (c != 0) && ram_write;
        wire tx_take = grant_pull && exec_context == (c != 0);
        wire rx_put = grant_push && exec_context == (c != 0);
        wire rx_take = rx_pop[c] && !rx_empty[c];
        always @(posedge clk or negedge rst_n) begin
            if (!rst_n) begin
                tx_rp[c] <= 0; tx_wp[c] <= 0;
                rx_rp[c] <= 0; rx_wp[c] <= 0;
            end else if (flush[c]) begin
                tx_rp[c] <= 0; tx_wp[c] <= 0;
                rx_rp[c] <= 0; rx_wp[c] <= 0;
            end else begin
                if (tx_put) tx_wp[c] <= tx_wp[c] + 1'b1;
                if (tx_take) tx_rp[c] <= tx_rp[c] + 1'b1;
                if (rx_put) rx_wp[c] <= rx_wp[c] + 1'b1;
                if (rx_take) rx_rp[c] <= rx_rp[c] + 1'b1;
            end
        end
    end endgenerate
endmodule
