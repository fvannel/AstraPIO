// SPDX-License-Identifier: Apache-2.0
`default_nettype none

// Mode 0, MSB first, one 32-bit transaction per CS assertion:
// [command:8][address:8][data:16]. 0x02 writes, 0x03 reads.
// Oversampling, not a separate SCK clock domain. See docs/compact-v3.md for limits.
module pio_spi #(parameter integer STUDY = 0) (
    input wire clk, rst_n,
    input wire sck, mosi, cs_n,
    output wire miso,
    output reg [7:0] address,
    output wire [15:0] write_data,
    output reg write_enable,
    output reg read_commit,
    output wire read_busy,
    input wire read_valid,
    input wire [15:0] read_data
);
    (* async_reg = "true" *) reg [1:0] sck_sync, mosi_sync, cs_sync;
    reg sck_previous;
    reg [5:0] count;
    reg command_read, command_write;
    reg burst_read;
    // A transaction either writes or reads: after receiving its header, the
    // same storage can hold incoming write data OR the outgoing read snapshot.
    reg [15:0] payload;
    reg miso_bit;
    reg snapshot_valid;

    wire rising_sck = sck_sync[1] & ~sck_previous;
    wire falling_sck = ~sck_sync[1] & sck_previous;
    // CS itself only masks the output; all state updates use synchronized CS.
    assign miso = (!cs_n && !cs_sync[1] && rst_n) ? miso_bit : 1'b0;
    assign write_data = payload;
    // Keep the RX head locked through the cycle that consumes read_commit.
    // Releasing at count==32 allowed a peer RECV to duplicate the host's byte.
    // CS deassertion terminates the lock even for an aborted transaction.
    assign read_busy = !cs_sync[1] && command_read && count >= 16;

    // Payload storage needs no reset: a command is decoded only after eight
    // received bits and read data is loaded before its first observable bit.
    // Write data remains stable at CS rise, until the next transaction shifts.
    always @(posedge clk) begin
        if (rst_n && !cs_sync[1]) begin
            if (rising_sck && count < 32 && (!command_read || count < 16))
                payload <= {payload[14:0], mosi_sync[1]};
            if (falling_sck && command_read) begin
                if (count == 16) payload <= {read_data[14:0], 1'b0};
                else if (count > 16 && count < 32)
                    payload <= {payload[14:0], 1'b0};
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sck_sync <= 0;
            mosi_sync <= 0;
            cs_sync <= 2'b11;
            sck_previous <= 0;
            count <= 0;
            command_read <= 0;
            command_write <= 0;
            burst_read <= 0;
            address <= 0;
            write_enable <= 0;
            read_commit <= 0;
            snapshot_valid <= 0;
            miso_bit <= 0;
        end else begin
            sck_sync <= {sck_sync[0], sck};
            mosi_sync <= {mosi_sync[0], mosi};
            cs_sync <= {cs_sync[0], cs_n};
            sck_previous <= sck_sync[1];
            write_enable <= 0;
            read_commit <= 0;
            if (cs_sync[1]) begin
                count <= 0;
                command_read <= 0;
                command_write <= 0;
                burst_read <= 0;
                miso_bit <= 0;
                snapshot_valid <= 0;
            end else begin
                if (rising_sck && count < 32) begin
                    count <= ((STUDY & 128) && burst_read && count == 31) ? 6'd16 : count + 1'b1;
                    if (count == 7) begin
                        command_read <= {payload[6:0], mosi_sync[1]} == 8'h03 ||
                            ((STUDY & 128) && {payload[6:0], mosi_sync[1]} == 8'h0b);
                        burst_read <= (STUDY & 128) && {payload[6:0], mosi_sync[1]} == 8'h0b;
                        command_write <= {payload[6:0], mosi_sync[1]} == 8'h02;
                    end
                    if (count == 15) begin
                        address <= {payload[6:0], mosi_sync[1]};
                        if (burst_read && {payload[6:0], mosi_sync[1]} != 8'h15) begin
                            command_read <= 0; burst_read <= 0;
                        end
                    end
                    if (count == 31 && command_write) begin
                        write_enable <= 1;
                    end
                    if (count == 31 && command_read)
                        read_commit <= snapshot_valid;
                end
                if (falling_sck) begin
                    if (count == 16 && command_read) begin
                        // Snapshot after address reception, before data clocks.
                        miso_bit <= read_data[15];
                        snapshot_valid <= read_valid;
                    end else if (count > 16 && count < 32 && command_read) begin
                        miso_bit <= payload[15];
                    end else begin
                        miso_bit <= 0;
                    end
                end
            end
        end
    end
endmodule
