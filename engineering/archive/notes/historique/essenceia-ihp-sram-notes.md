---
draft: true
---

Power connection wasn't being made. 

I am using the default hierarchical macro instegration. 
My design's main power is on TopMetal1, and I was expecting SRAM power ports to be on layer N-1, so Metal5. 
Yet looking at the SRAM macro lef file shows me that power is actually expected on Metal4. 

https://github.com/IHP-GmbH/IHP-Open-PDK/blob/a2bf8ea81aee7d0fcdd6d62168edca0d7d0bcb08/ihp-sg13g2/libs.ref/sg13g2_sram/lef/RM_IHPSG13_1P_256x8_c3_bm_bist.lef#L146C1-L153C8

Good problem to have, since this means I can integreate SRAM as a 2 layer deep macro.
Problem is: how do I drop the expected power grid one more layer ? 

Currently the OpenROAD power delievery network grid builder doesn't find the pad: 
```
[09:20:27] WARNING  [PDN-0232] The grid "macro - m_ihp_sram" (Instance) does not contain any shapes or vias.                                                                                                                                                       openroad.py:297
[09:20:27] ERROR    [PDN-0233] Failed to generate full power grid.  
```

This is only made more puzzling to me as I think I am already creating a connection: 
```
            add_global_connection \
                -net $power_net \
                -inst_pattern $instance_name \
                -pin_pattern $power_pin \
                -power
```
Global connection might not mean what I think it means... 


I asked for help un-stupidding myself on the Tiny Tapeout discord and tnt jumped in pointing me to this missmatch in power connection layers. 
Then mole99 also dropped by and pointed me to the crown jewel I was looking for: an example of an full IHP chip (using the new librelane chip flow) that just so happened to be using the SAME SRAM MACRO !!!! 

Alright, calm my exitement, not exactly the same macro, but of the same family, aka: Close enogth !  

And guess what, he has a custon PDN tcl script for setting the power delivery to these SRAM MACROS, which I will now proceed to unshamfully wripe off. 
https://github.com/IHP-GmbH/ihp-sg13g2-librelane-template/blob/da17746e19984826dd780ce778b6bb40dbf54544/librelane/config.yaml#L196


Oh yeah baby, here we go! We have found the magical missing ingrediant: 
```tcl
define_pdn_grid \
    -macro \
    -instances "\
    i_chip_core.sram_0" \
    -name sram_NS \
    -starts_with POWER

add_pdn_stripe \
    -grid sram_NS \
    -layer Metal5 \
    -width 2.81 \
    -pitch 11.24 \
    -offset 2.81 \
    -spacing 2.81 \
    -nets "VSS VDD" \
    -starts_with POWER

add_pdn_connect \
    -grid sram_NS \
    -layers "Metal4 Metal5"
add_pdn_connect \
    -grid sram_NS \
    -layers "Metal5 TopMetal1"
```

My version : 
```
define_pdn_grid \
    -macro \
    -instances "m_ihp_sram" \
    -name sram_NS \
    -starts_with POWER

add_pdn_stripe \
    -grid sram_NS \
    -layer Metal5 \
    -width 2.81 \
    -pitch 11.24 \
    -offset 2.81 \
    -spacing 2.81 \
    -nets "VGND VPWR" \
    -starts_with POWER

add_pdn_connect \
    -grid sram_NS \
    -layers "Metal4 Metal5"

add_pdn_connect \
    -grid sram_NS \
    -layers "Metal5 TopMetal1"
```
So what is this party all about ? 

#### Defining a new power grid 

Create a new power grid over the `m_ihp_sram` macro called `sram_NS`, with the first strap being `POWER` (default is `GROUND`). 
The reference to the macro instance is used for defining of this new power grid's area. 
```
define_pdn_grid \
    -macro \
    -instances "m_ihp_sram" \
    -name sram_NS \
    -starts_with POWER
```

#### Adding stripes

Recall how the macro expects power on `Metal4` and we have power on `TopMetal1` ? 
This step adds a power grid to the intermediary `Metal5` layer to help bridge the gap. 

Define a pattern of the power and ground stripes to be added to `Metal5` in the `sram_NS` grid.
The `width`, `pitch`, `offset` and `spacing` parameters are used to define the straps topology. 
They must be sized wide enoght and be plentifull enoght to provide sufficient power accross the
entire maco, even during heavy load (hello IR drop, I did not miss you). 

These stripes are likely oversized to prevent any headacks. 
```
add_pdn_stripe \
    -grid sram_NS \
    -layer Metal5 \
    -width 2.81 \
    -pitch 11.24 \
    -offset 2.81 \
    -spacing 2.81 \
    -nets "VGND VPWR" \
    -starts_with POWER
```


Static IR drop analysis shows we are A OK, though I am forced to recognise a complete analysis would also encoupase a IR dynamic drop analysis.

`VPWR` report : 
```
########## IR report #################
Net              : VPWR
Corner           : nom_typ_1p20V_25C
Total power      : 3.05e-04 W
Supply voltage   : 1.20e+00 V
Worstcase voltage: 1.20e+00 V
Average voltage  : 1.20e+00 V
Average IR drop  : 1.25e-06 V
Worstcase IR drop: 9.84e-05 V
Percentage drop  : 0.01 %
######################################
```

`VGND` report : 
```
########## IR report #################
Net              : VGND
Corner           : nom_typ_1p20V_25C
Total power      : 3.05e-04 W
Supply voltage   : 0.00e+00 V
Worstcase voltage: 9.42e-05 V
Average voltage  : 1.22e-06 V
Average IR drop  : 1.22e-06 V
Worstcase IR drop: 9.42e-05 V
Percentage drop  : 0.01 %
######################################
```

#### Connecting the sram power grid to main power grid 

In this process, there is no district level authority to inspect my installation before 
connecting it to the grid, unlike if I was to install a solar array on my roof. 

All that is left is to call `add_pdn_connection` to hook up the `VPWR` and `VGND` power nets from my 
newly defined `sram_NS` grid to the corresponding power nets on `Metal4` and `TopMetal1`. 

```
add_pdn_connect \
    -grid sram_NS \
    -layers "Metal4 Metal5"

add_pdn_connect \
    -grid sram_NS \
    -layers "Metal5 TopMetal1"
```

#### Results 

`TopMetal1`, represented in light blue, is the project's main power grid extending over all of the core, and
is now connected to our newly defined `sram_NS` grid.

In red we can see the custom straps we have added to `Metal5` now bridging `TopMetal1` and the SRAMs macro's own 
power straps on `Metal4`, prepresented in green. 

![final power grid](final_power_grid.png)
