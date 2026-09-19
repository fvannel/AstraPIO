// SPDX-License-Identifier: Apache-2.0
`default_nettype none
// Shared configurable pulse-I/O engine. All state uses the main ASIC clock.
module pio_timed #(parameter integer STUDY = 0) (
    input wire clk, rst_n,
    input wire [12:0] inputs,
    input wire [13:0] occupied,
    input wire [3:0] address,
    input wire [15:0] write_data,
    input wire write_enable,
    output reg [15:0] read_data,
    output wire [13:0] claim,
    output wire serial_out,
    output wire irq
);
    reg enabled, output_enabled, replace_prefix;
    reg [1:0] timed_mode;
    wire event_mode = (STUDY & 32) && timed_mode == 1;
    wire capture_mode = (STUDY & 64) && timed_mode == 2;
    reg [3:0] input_pin, output_pin;
    reg [15:0] idle_limit, idle_left;
    reg [5:0] sample_delay, launch_delay, high_zero, high_one;
    reg [4:0] prefix_length, remaining;
    reg armed, in_frame, capture_frame, input_previous, sampling;
    reg [5:0] age;
    reg [23:0] received;
    reg [23:0] shadow, active_word;
    reg [1:0] shadow_initialized;
    reg pending, active_valid, sampled_bit, dout;
    reg [5:0] pulse_left;
    reg rx_valid, host_error, overrun, timing_error;
    wire din = inputs[input_pin];
    wire trigger_input = capture_mode ? inputs[output_pin] : din;
    wire rise = trigger_input && !input_previous;
    wire [13:0] output_mask = 14'b1 << output_pin;
    assign claim = enabled && output_enabled ? output_mask : 14'b0;
    assign serial_out = enabled && output_enabled && dout;
    assign irq = rx_valid || host_error || overrun || timing_error;
    wire control_ok = (write_data & 16'hf8f8) == 0 &&
        !(event_mode && write_data[2]) &&
        !(capture_mode && (write_data[2:1] != 0 || (write_data[0] && output_pin > 12))) &&
        !(event_mode && write_data[0] && high_zero >= idle_limit) &&
        !(write_data[0] && write_data[1] && |(occupied & output_mask)) &&
        !(enabled && write_data[0] && write_data[2:1] != {replace_prefix,output_enabled}) &&
        !(write_data[0] && write_data[1] && write_data[2] && !active_valid && !pending && !write_data[9]) &&
        !(write_data[9] && (pending || !(&shadow_initialized)));
    wire stop = write_enable && address == 1 && control_ok && !write_data[0];
    wire sample_now = enabled && sampling && age == sample_delay;
    wire launch_now = enabled && sampling && age == launch_delay;
    wire outgoing_bit = replace_prefix && remaining != 0 ? active_word[remaining-1'b1] : sampled_bit;

    always @* begin
        read_data = 0;
        case (address)
            4'h0: read_data = 16'h5449;
            4'h1: read_data = {13'b0,replace_prefix,output_enabled,enabled};
            4'h2: read_data = {8'b0,output_pin,input_pin};
            4'h3: read_data = idle_limit;
            4'h4: read_data = {2'b0,launch_delay,2'b0,sample_delay};
            4'h5: read_data = {2'b0,high_one,2'b0,high_zero};
            4'h6: read_data = {11'b0,prefix_length};
            4'h7: read_data = shadow_initialized[0] ? shadow[15:0] : 16'b0;
            4'h8: read_data = shadow_initialized[1] ? {8'b0,shadow[23:16]} : 16'b0;
            4'h9: read_data = rx_valid ? received[15:0] : 16'b0;
            4'ha: read_data = rx_valid ? {8'b0,received[23:16]} : 16'b0;
            4'hb: read_data = {8'b0,timing_error,overrun,host_error,active_valid,pending,rx_valid,in_frame,armed};
            4'hc: read_data = 16'h0118;
            4'hd: if (STUDY & (32|64)) read_data = {14'b0,timed_mode};
            default: read_data = 0;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            enabled <= 0; output_enabled <= 0; replace_prefix <= 0;
            timed_mode <= 0;
            input_pin <= 0; output_pin <= 8; idle_limit <= 15000;
            sample_delay <= 25; launch_delay <= 32; high_zero <= 16; high_one <= 32;
            prefix_length <= 24; remaining <= 0; idle_left <= 0;
            armed <= 0; in_frame <= 0; capture_frame <= 0;
            input_previous <= 0; sampling <= 0; age <= 0;
            rx_valid <= 0; host_error <= 0; overrun <= 0; timing_error <= 0;
            pending <= 0; active_valid <= 0; sampled_bit <= 0; dout <= 0; pulse_left <= 0;
            shadow_initialized <= 0;
        end else begin
            input_previous <= trigger_input;
            if (dout && (!event_mode || rise)) begin
                if (pulse_left == 1) begin dout <= 0; pulse_left <= 0; end
                else pulse_left <= pulse_left - 1'b1;
            end
            if (write_enable) begin
                case (address)
                    4'h1: begin
                        if (!control_ok) host_error <= 1;
                        else begin
                            enabled <= write_data[0]; output_enabled <= write_data[1];
                            replace_prefix <= write_data[2];
                            if (write_data[8]) rx_valid <= 0;
                            if (write_data[9]) pending <= 1;
                            if (write_data[10]) begin host_error <= 0; overrun <= 0; timing_error <= 0; end
                        end
                    end
                    4'h2: if (!enabled && write_data[15:8] == 0 && write_data[3:0] <= 12 && write_data[7:4] <= 13) begin
                        input_pin <= write_data[3:0]; output_pin <= write_data[7:4];
                    end else host_error <= 1;
                    4'h3: if (!enabled && write_data != 0) idle_limit <= write_data; else host_error <= 1;
                    4'h4: if (!enabled && (write_data & 16'hc0c0) == 0 && write_data[5:0] != 0 && write_data[13:8] > write_data[5:0]) begin
                        sample_delay <= write_data[5:0]; launch_delay <= write_data[13:8];
                    end else host_error <= 1;
                    4'h5: if (!enabled && (write_data & 16'hc0c0) == 0 && write_data[5:0] != 0 && write_data[13:8] != 0) begin
                        high_zero <= write_data[5:0]; high_one <= write_data[13:8];
                    end else host_error <= 1;
                    4'h6: if (!enabled && write_data >= 1 && write_data <= 24) prefix_length <= write_data[4:0]; else host_error <= 1;
                    4'h7: if (pending) host_error <= 1; else shadow_initialized[0] <= 1;
                    4'h8: if (pending || write_data[15:8] != 0) host_error <= 1; else shadow_initialized[1] <= 1;
                    4'hd: if (!enabled && (STUDY & (32|64)) &&
                                (write_data == 0 || (write_data == 1 && (STUDY & 32)) ||
                                 (write_data == 2 && (STUDY & 64))))
                        timed_mode <= write_data[1:0];
                        else host_error <= 1;
                    default: host_error <= 1;
                endcase
            end
            if (!enabled || stop) begin
                idle_left <= idle_limit; armed <= 0; in_frame <= 0;
                sampling <= 0; remaining <= 0; capture_frame <= 0;
                dout <= 0; pulse_left <= 0;
            end else if (capture_mode) begin
                // Input-only fixed-period sampler. Output selector is the
                // separate trigger input; the existing 24-bit RX bank is reused.
                if (rise && !in_frame) begin
                    in_frame <= 1; sampling <= 1; age <= 1;
                    remaining <= prefix_length; capture_frame <= !rx_valid;
                    if (rx_valid) overrun <= 1;
                end else if (in_frame) begin
                    if (rise) timing_error <= 1;
                    if (sample_now) begin
                        remaining <= remaining - 1'b1;
                        if (remaining == 1) begin
                            if (capture_frame) rx_valid <= 1;
                            in_frame <= 0; sampling <= 0;
                        end
                    end
                    age <= age == launch_delay ? 6'd1 : age + 1'b1;
                end
            end else if (event_mode) begin
                // Same 16-bit countdown and 6-bit pulse counter, edge timebase.
                if (rise) begin
                    if (idle_left <= 1) begin
                        idle_left <= idle_limit;
                        dout <= 1; pulse_left <= high_zero;
                    end else idle_left <= idle_left - 1'b1;
                end
            end else begin
                // Countdown avoids a 16-bit magnitude comparator and a second
                // subtractor. Zero holds the qualification until a new edge.
                if (din) idle_left <= idle_limit;
                else if (idle_left != 0) idle_left <= idle_left - 1'b1;
                if (!din && idle_left == 1) begin
                    armed <= 1; in_frame <= 0; sampling <= 0; remaining <= 0;
                    dout <= 0; pulse_left <= 0;
                end else begin
                    if (rise && (armed || in_frame)) begin
                        if (sampling) begin
                            timing_error <= 1; in_frame <= 0; armed <= 0;
                            sampling <= 0; dout <= 0; pulse_left <= 0;
                        end
                        else begin
                            sampling <= 1; age <= 1;
                            if (armed) begin
                                armed <= 0; in_frame <= 1; remaining <= prefix_length;
                                capture_frame <= !rx_valid;
                                if (rx_valid) overrun <= 1;
                                if (pending) begin pending <= 0; active_valid <= 1; end
                            end
                        end
                    end
                    else if (sampling) begin
                        age <= age + 1'b1;
                        if (sample_now) begin
                            sampled_bit <= din;
                            if (remaining == 1 && capture_frame) rx_valid <= 1;
                        end
                        if (launch_now) begin
                            sampling <= 0;
                            if (remaining != 0) remaining <= remaining - 1'b1;
                            if (output_enabled) begin
                                if (dout) begin
                                    timing_error <= 1; in_frame <= 0; armed <= 0;
                                    dout <= 0; pulse_left <= 0;
                                end else begin
                                    dout <= 1;
                                    pulse_left <= outgoing_bit ? high_one : high_zero;
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    // Payload only becomes observable after every configured bit was captured.
    // No reset needed; clear at the first sample, not on every idle clock.
    always @(posedge clk) begin
        if (rst_n && sample_now && (!rise || capture_mode) && !stop && remaining != 0 && capture_frame) begin
            if (remaining == prefix_length) received <= {23'b0,din};
            else received <= {received[22:0],din};
        end
        if (rst_n && enabled && !stop && armed && rise && pending) active_word <= shadow;
        if (rst_n && write_enable && !pending) begin
            if (address == 7) shadow[15:0] <= write_data;
            if (address == 8 && write_data[15:8] == 0) shadow[23:16] <= write_data[7:0];
        end
    end
endmodule
