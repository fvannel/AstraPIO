// SPDX-License-Identifier: Apache-2.0
`default_nettype none

// Mode 0, MSB first, one 32-bit transaction per CS assertion:
// [command:8][address:8][data:16]. 0x02 writes, 0x03 reads.
// Oversampling, not a separate SCK clock domain. See docs/isa-v0.md for limits.
module pio_spi (
    input wire clk, rst_n,
    input wire sck, mosi, cs_n,
    output wire miso,
    output reg [7:0] address,
    output reg [15:0] write_data,
    output reg write_enable,
    input wire [15:0] read_data
);
    (* async_reg = "true" *) reg [1:0] sck_sync, mosi_sync, cs_sync;
    reg sck_previous;
    reg [5:0] count;
    reg [7:0] command;
    reg [15:0] rx_shift, tx_shift;
    reg miso_bit;

    wire rising_sck = sck_sync[1] & ~sck_previous;
    wire falling_sck = ~sck_sync[1] & sck_previous;
    // CS itself only masks the output; all state updates use synchronized CS.
    assign miso = (!cs_n && !cs_sync[1] && rst_n) ? miso_bit : 1'b0;

    always @(posedge clk) begin
        if (!rst_n) begin
            sck_sync <= 0;
            mosi_sync <= 0;
            cs_sync <= 2'b11;
            sck_previous <= 0;
            count <= 0;
            command <= 0;
            address <= 0;
            write_data <= 0;
            write_enable <= 0;
            rx_shift <= 0;
            tx_shift <= 0;
            miso_bit <= 0;
        end else begin
            sck_sync <= {sck_sync[0], sck};
            mosi_sync <= {mosi_sync[0], mosi};
            cs_sync <= {cs_sync[0], cs_n};
            sck_previous <= sck_sync[1];
            write_enable <= 0;
            if (cs_sync[1]) begin
                count <= 0;
                command <= 0;
                rx_shift <= 0;
                tx_shift <= 0;
                miso_bit <= 0;
            end else begin
                if (rising_sck && count < 32) begin
                    rx_shift <= {rx_shift[14:0], mosi_sync[1]};
                    count <= count + 1'b1;
                    if (count == 7)
                        command <= {rx_shift[6:0], mosi_sync[1]};
                    if (count == 15)
                        address <= {rx_shift[6:0], mosi_sync[1]};
                    if (count == 31 && command == 8'h02) begin
                        write_data <= {rx_shift[14:0], mosi_sync[1]};
                        write_enable <= 1;
                    end
                end
                if (falling_sck) begin
                    if (count == 16 && command == 8'h03) begin
                        // Snapshot after address reception, before data clocks.
                        miso_bit <= read_data[15];
                        tx_shift <= {read_data[14:0], 1'b0};
                    end else if (count > 16 && count < 32 && command == 8'h03) begin
                        miso_bit <= tx_shift[15];
                        tx_shift <= {tx_shift[14:0], 1'b0};
                    end else begin
                        miso_bit <= 0;
                    end
                end
            end
        end
    end
endmodule
