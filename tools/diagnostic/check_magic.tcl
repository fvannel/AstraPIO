# Diagnostic only. SRAM read/check reproducer with explicit DRC completion.
# No layout is written; no category, region or SRAM cell is suppressed.
proc astra_step {name script} {
    set start [orig_clock milliseconds]
    puts stdout "ASTRA_STAGE $name BEGIN $start"
    flush stdout
    set value [uplevel 1 $script]
    puts stdout "ASTRA_STAGE $name END [expr {[orig_clock milliseconds] - $start}]ms"
    flush stdout
    return $value
}
crashbackups disable
locking disable
units internal
snap internal
gds noduplicates true
gds readonly true
astra_step import_setup {source $env(ASTRA_FLATGLOB)}
gds maskhints yes
astra_step read_gds {gds read $env(ASTRA_INPUT)}
magic::suspendall
astra_step load_top {load $env(ASTRA_TOP)}
astra_step select_top {select top cell}
astra_step cover_top {
    box values {*}[select bbox]
    puts stdout "ASTRA_CHECK_BOX [box values]"
}
astra_step expand {expand}
astra_step euclidean {drc euclidean on}
astra_step drc_style {drc style drc(full)}
astra_step drc_check {drc check}
astra_step drc_catchup {drc catchup}
# Error markers can extend outside the geometry (e.g. a too-thin wire).
# Expand the report window, not the layout or DRC rule halo.
astra_step report_window {box grow c 100um}
set global_count [astra_step global_count {drc listall count total}]
puts stdout "ASTRA_DRC_GLOBAL $global_count"
puts stdout "ASTRA_DRC_CELLS [drc listall count]"
puts stdout "ASTRA_DRC_TOP [drc list count total]"
set results [astra_step list_results {drc listall why}]
puts stdout "ASTRA_DRC_GLOBAL_AFTER_WHY [drc listall count total]"
set raw [open $env(ASTRA_RAW_REPORT) w]
puts $raw $results
close $raw
set report [open $env(ASTRA_REPORT) w]
set total 0
foreach {rule boxes} $results {
    set n [llength $boxes]
    incr total $n
    puts $report "$n\t$rule"
    puts stdout "ASTRA_DRC_CATEGORY $n $rule"
}
puts $report "TOTAL\t$total"
puts stdout "ASTRA_DRC_TOTAL $total"
close $report
puts stdout "ASTRA_DRC_COMPLETE $total"
flush stdout
if {$total == 0 && $global_count != 0} {
    puts stderr "Global DRC errors exist outside the report window; result is incomplete."
    exit 2
}
if {$total > 0} {exit 1}
exit 0
