// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// Four independent two-byte queues. Host RX snapshots exclude peer RECV until
// the SPI read ends; simultaneous full pop/push is supported by pio_fifo.
module pio_queues (
    input wire clk, rst_n,
    input wire [1:0] flush,
    input wire host_context, host_tx_write, host_rx_pop, host_rx_lock,
    input wire [7:0] host_data,
    input wire exec_context, exec_pull, exec_push, exec_recv,
    input wire [7:0] exec_data,
    output wire pull_accept, push_accept, recv_accept, overflow,
    output wire [7:0] pull_data, peer_data, host_rx_data,
    output wire [1:0] rx_available,
    output wire [15:0] host_status
);
    wire [1:0] tx_empty, tx_full, tx_ready, rx_empty, rx_full, rx_ready;
    wire [7:0] tx_q [0:1], rx_q [0:1];
    wire [1:0] tx_level [0:1], rx_level [0:1];
    assign rx_available = ~rx_empty;
    assign pull_accept = exec_pull && !tx_empty[exec_context] && !flush[exec_context];
    assign push_accept = exec_push && rx_ready[exec_context] && !flush[exec_context];
    assign recv_accept = exec_recv && !rx_empty[!exec_context] && !flush[!exec_context]
        && !(host_rx_lock && host_context != exec_context);
    assign overflow = host_tx_write && !flush[host_context] && !tx_ready[host_context];
    assign pull_data = tx_q[exec_context];
    assign peer_data = rx_q[!exec_context];
    assign host_rx_data = rx_q[host_context];
    // ABI v3: [15:14] RX level, [13:12] TX level, [3:0] RXfull/RXempty/TXfull/TXempty.
    assign host_status = {rx_level[host_context], tx_level[host_context], 8'b0,
        rx_full[host_context], rx_empty[host_context], tx_full[host_context], tx_empty[host_context]};
    genvar ctx;
    generate for (ctx = 0; ctx < 2; ctx = ctx + 1) begin : contexts
        pio_fifo #(.WIDTH(8), .ADDR_BITS(1)) tx (
            .clk(clk), .rst_n(rst_n), .flush(flush[ctx]),
            .push(host_tx_write && host_context == ctx),
            .pop(pull_accept && exec_context == ctx), .data_in(host_data),
            .data_out(tx_q[ctx]), .empty(tx_empty[ctx]), .full(tx_full[ctx]),
            .push_ready(tx_ready[ctx]), .level(tx_level[ctx])
        );
        pio_fifo #(.WIDTH(8), .ADDR_BITS(1)) rx (
            .clk(clk), .rst_n(rst_n), .flush(flush[ctx]),
            .push(push_accept && exec_context == ctx),
            .pop((host_rx_pop && host_context == ctx) || (recv_accept && exec_context != ctx)),
            .data_in(exec_data), .data_out(rx_q[ctx]),
            .empty(rx_empty[ctx]), .full(rx_full[ctx]), .push_ready(rx_ready[ctx]), .level(rx_level[ctx])
        );
    end endgenerate
endmodule
