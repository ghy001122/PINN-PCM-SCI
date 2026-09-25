# Validation and execution deviations

The scientific object is the fixed E/29 base plus one of the three prescribed zero-initialized corrections. No old checkpoint, reference, phase equation, support interval, temperature field, calibration or optimizer budget was changed.

## Completed numerical qualification

The actual-checkpoint test suite passed seven initial tests, then one added spline/full-gradient intervention test. Two inherited observation-visibility/importance-weight tests and two original L-BFGS tests also passed. Raw available logs and the initial seven-test execution record are retained under `outputs/runs/20260924-observation-preserving-phase/`.

These checks cover: exact zero-correction identity; C2 support and visible/powered-time invariance; nonzero finite observation-preserving changes; complete latent and cached derivative composition; unchanged original objective at the base; full/reduced objective-gradient agreement for N/S; latent heat identity; powered G electrical VJP; independent spline value/first/second derivative and coefficient-gradient checks; sampling mass; hidden-label exclusion; and restoration of the last accepted L-BFGS state. There were no training optimizer updates in these tests. They validate implementation and do not establish a prediction gain.

At the predeclared finite output-bias perturbation 0.125, the measured N observation-gradient norm is exactly zero, while its physical-gradient norm is 0.0124373. The G observation-gradient norm is 2.13180×10^−5; the N/G total-gradient difference norm is 0.146497 and their cosine is 0.909321. This is a bounded real-interface intervention on a small diagnostic pool, not a full-profile performance comparison or evidence that the eventual trajectories improve state accuracy.

The common fixed-pool preparation was aligned to one RNG stream with seed 750129 before any profile or optimizer step. The separate D/complement training RNG streams retain seeds 740129 and 740229. The alignment record is retained, including the fact that no earlier trajectory consumed the draft pool.

## Two local profile failures

The first G full objective/gradient completed but its Windows memory-recording call lacked the proper HANDLE argument type. The objective/gradient values and coordinate counts were not saved; 50 electrical forward/adjoint solves are known from the completed fixed pool. After the isolated metadata repair, the next attempt failed partway through because local memory was exhausted. No optimizer step occurred in either attempt. The incomplete attempt's full work is unknown and is not counted as zero.

The remaining zero-update profiles were executed sequentially on the already authorized cloud instance's CPU, with the same frozen inputs. One complete remote profile per arm passed. Thus G has two completed full objective/gradient passes in total plus one incomplete engineering attempt; N/S each have one. No dependency was installed or upgraded. The first failure's contemporaneous planned recovery wording is historical; the second failure and final remote recovery supersede it explicitly.

## Device propagation error

The cloud launch requested cuda:0 and its independent CUDA preflight passed, but the training function omitted the device argument when constructing the experiment. Consequently G/N/S train on the Intel Xeon Gold 6130 CPU (2.10 GHz; four Torch threads, one OpenBLAS thread). The omission was detected during G, before reference scoring. The active process was allowed to finish all branches on the same CPU; there was no restart, extra optimization or mixed-device comparison. A separate local fix now forwards and verifies the device, while the executed runner and source archive remain preserved.

A targeted post-fix regression passed in 0.017 s. It requires the requested device at the experiment factory and deliberately stops before model construction or any optimizer step; the original omitted argument fails this test. This additional engineering test is separate from the twelve pre-training qualification checks.

The audit/native-reader entrypoint explicitly passes cuda:0. Its GPU work is distinct from CPU training. The Tesla V100-PCIE 32GB instance is recovered and shut down at the end of that sequence. `compute-closure.json` records the actual transfer, verification and shutdown observations; the public excerpt omits connection information. Neither a launch argument nor GPU availability is used as evidence of actual training placement.

## Post-lock checks

The evaluator verifies N/S own-field electrical spots before composing full arrays, checks exact equality of inherited temperature/port metrics and outside-window phase metrics, and verifies both heated-window event supports, onset, recall, precision and active masses. All three endpoints must be locked before any new reference scoring. G has its own complete native readout. The result module reports physical qualification separately from state accuracy and flags the actual resource deviation rather than treating CPU execution as new scientific evidence.
