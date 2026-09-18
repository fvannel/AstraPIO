# Diagnostic only. SRAM read/check reproducer with explicit DRC completion.
# No layout is written; no category, region or SRAM cell is suppressed.
crashbackups disable
locking disable
units internal
gds noduplicates true
gds readonly true
source $env(ASTRA_FLATGLOB)
gds maskhints yes
gds read $env(ASTRA_INPUT)
magic::suspendall
load $env(ASTRA_TOP)
select top cell
expand
drc euclidean on
drc style drc(full)
drc check
drc catchup
set results [drc listall why]
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
if {$total > 0} {exit 1}
exit 0
