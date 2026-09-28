# Clarification of voltage and current measurements in five thermal coupling records

We are preparing a software analysis of the public thermal neuristor records associated with *Collective dynamics and long-range order in thermal neuristor networks*. Before applying an RC reconstruction, we would appreciate clarification of the measurement circuit for the following files in `data/thermal_coupling/`:

1. `Ben012_1_325K_1E3_12k_2.6V_1E2_12K_2.6V_sync_000_ALL.csv`
2. `Ben012_1_325K_1E3_12k_4.1V_1E2_12K_3.7V_sync_000_ALL.csv`
3. `Ben012_1_325K_1E3_12k_4.1V_1E2_12K_4V_sync_000_ALL.csv`
4. `Ben012_1_325K_1E3_12k_4V_1E2_12K_2.6V_sync_000_ALL.csv`
5. `Ben012_1_325K_1E3_12k_5V_1E2_12K_2.6V_sync_000_ALL.csv`

We retain the device identities **1E3** and **1E2** from the filenames. The supplied channel convention identifies CH1/CH4 as the two voltage channels and CH2/CH3 as voltage drops across 50 Ω. It does not by itself establish which current branch the latter channels measure.

Could you clarify the following, noting any differences among these five records?

1. **Nodes and wiring.** What are the positive and negative terminals and reference ground for each channel? A circuit or annotated wiring diagram showing each 50 Ω termination relative to the device, capacitance and load would be especially helpful. Does each current channel measure device current, total load current including capacitor charging, or another branch? Does obtaining the capacitor-node voltage from CH1/CH4 require a current-dependent voltage-drop correction?
2. **Drive and timing.** Are the filename voltages constant throughout the saved interval? If there are switching edges, what are their times and the trigger's meaning relative to the source waveform? Please identify the voltage/current channel gains, polarities and known relative delays or deskew settings.
3. **Capacitance and load.** Is there a measured or estimated capacitance for each device with this cabling and acquisition setup, and was the setup unchanged between records? What is its source or estimation procedure? Do the stated 12 kΩ loads include any additional series resistance or measurement termination?

These details would let us distinguish (I_{load}=(V_{in}-v)/R_L), (I_C=C\dot v), and (I_{device}=I_{load}-I_C) where that topology is applicable. We are not assuming the high-threshold fitted model's capacitance applies to these records. An existing diagram or setup note is sufficient; no unpublished manuscript or private waveform transfer is requested.

Thank you for your clarification.

**Separate future calibration condition.** If topology, gain, timing and the device-current branch are confirmed and only C is missing, a separately approved development analysis could estimate a constant C from (z_j=C\Delta v_j), using predefined intervals and the same device/wiring grouping. It would not jointly fit wiring, arbitrary delays, gain, per-protocol C or thermal parameters. Calibration current would be disclosed as development input. The 4.1/3.9 V protocol remains excluded from observations, calibration and scoring.
