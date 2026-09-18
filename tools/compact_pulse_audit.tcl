# Supplemental audit of the frozen, officially routed compact candidate.
# Not a replacement for any Tiny Tapeout check; no timing exception is added.
set sta_continue_on_error 0
if {[catch {
    set model $::env(ASTRA_LIB_CORNER)
    set artifact work/compact-audit/submission/tt_submission
    set final work/compact-audit/logs/runs/wokwi/final
    read_liberty work/compact-audit/pdk/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_${model}.lib
    read_verilog $artifact/tt_um_fabien_pio.v
    link_design tt_um_fabien_pio
    read_sdc $final/sdc/tt_um_fabien_pio.sdc
    # write_sdc omits the flow's derating; restore exactly the base.sdc values.
    set_timing_derate -early 0.95
    set_timing_derate -late 1.05
    read_spef $artifact/tt_um_fabien_pio.nom.spef
    puts "ASTRA_PULSE_BEGIN $model"
    report_check_types -min_pulse_width -verbose -digits 6
    puts "ASTRA_PULSE_VIOLATORS_BEGIN $model"
    report_check_types -min_pulse_width -violators -verbose -digits 6
    puts "ASTRA_PULSE_END $model"
    report_checks -path_delay min_max -group_path_count 1 -digits 6
} message options]} {
    puts stderr "ASTRA_AUDIT_ERROR: $message"
    puts stderr [dict get $options -errorinfo]
    exit 1
}
exit 0
