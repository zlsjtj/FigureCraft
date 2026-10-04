# Laboratory-style source notes — constructed DEMO only

These notes and values are fictional but internally fixed input for a skill evaluation. No experiment was run. All prior-art entries below are internal design records, not published literature. Do not call a mechanism novel on this basis.

## Geometry sheet (illustrative shape and topology are specified)

The specimen is one rectangular opaque strip, 60 mm long along x, 10 mm wide along y, and 1 mm thick. This is a mechanical demonstration, not a claim about a named material. Two narrow supports are attached to one base: one under the strip at x=8 mm and one at x=52 mm. The strip lies horizontally above the base, its central span unsupported. The microscope looks from above at two surface fiducials. One small circular mark is at x=20 mm, the other at x=40 mm; both on the strip centerline. No light beam or optical path was modeled. Do not add one.

In C, a fixed upright pin at the left support fits a round locating hole in the strip. A second upright pin at the right support passes through a longitudinal slot along x in the strip. The slot permits a specified ±0.40 mm of strip travel relative to that pin from the assembly position. Slot width limits transverse movement. A narrow leaf spring fixed to the right support presses down on the strip beside the slot, not through it; the slot opening remains visible. The clip is released for removal. A washer on the left keeps the strip seated on its round datum. There is no new base, sensor, thermal controller or numerical correction in C. The pin-and-slot scheme already appears in record R0. No exact pin diameter, spring curvature or screw thread was fixed; any illustration should use simplified shape, not fabricated manufacturing dimensions. Do not infer stress or a coefficient of expansion from hot travel.

The two supports in A both use round locating holes and screw seating. B keeps the left round datum and the same slotted right geometry as C but has no downward leaf retention at the right. D is built from C; after indexing it, a screw locks axial travel at the right slot. C and D use the same nominal leaf setting; D adds the axial lock. These are fixture configurations on separate trials, not four specimens stacked together.

## Assembly observations and bounds

The operator centers the right pin in its slot with a removable jig, seats the left datum, applies the leaf clip, then removes the jig. A feeler gauge verifies travel clearance; leaving the jig in would constrain motion, so it is absent during cycling. C uses the round datum to establish position, the slot for axial allowance, and the leaf for vertical seating. These roles are design intent; no force or friction data were collected. The clip does not imply zero friction.

A hot image displacement is expected when the strip moves; it is recorded separately from residual misregistration after cooling. The table's post-cooling drift and hot height lift are different physical quantities. Fiducial processing is identical for all configurations, same magnification and exposure; no registration correction is applied before calculating drift. Empty-holder image drift ranged from 2 to 4 µm across the session; it is an instrument check, not subtracted from any row. Do not treat it as an uncertainty estimate.

Two thermal schedules: T1 from 25 to 80 °C and back to 25 °C; T2 from 25 to 140 °C and back. Ramp 2 °C/min; hot dwell 10 min; measurements after return to 25 °C and a further 10 min. The hot stage, schedule, fiducial code and illumination were inherited from R1. The stage was not changed. Six separate strip installations per configuration per schedule, three cycles per installation. Maxima and medians are provided per installation over its three cycles; a later aggregate must say exactly what it summarizes. No random order was recorded. Do not report p-values, independent cycle counts of n=18, confidence intervals or long-term service reliability.

The application limits were recorded before this demonstration: after cooling, absolute fiducial registration error must be no more than 30 µm; at the hot dwell, out-of-plane lift must be no more than 8 µm; fractures are unacceptable. The two criteria serve different parts of image comparability. A method does not qualify by passing only one. Full measured stress, thermal conductivity and actual device performance were not recorded.

## Source ledger

R0: internal fixture handbook, revision A (constructed). Existing round datum + longitudinal slot design prevents geometric overconstraint along the long direction, as a design principle. No cyclic imaging results or leaf-retained version in this record. This is the source for inherited pin/slot geometry, not a verified literature novelty claim.
R1: internal microscope routine, revision 3 (constructed). Same two-fiducial displacement estimator, heating stage, imaging setup and schedules. Previous fixture A was screw-seated at both ends. R1 contains no comparison to C.
R2: this demonstration assembly log. The removable centering jig, clearance check, releasable leaf and combined cycling comparison are recorded here. Setup time was not measured; do not say quick, low-cost or easy-to-manufacture based on script length or part count. The parts are conventional.
R3: this demonstration results.csv, one row per installation, 48 rows. All rows are retained, including low-temperature success of A, height failures of B and axial-lock failures of D. No dynamic stress trace exists.

## Separate checks not in the timing/result table

Twelve deliberate assembly checks on C: in six, the centering jig was deliberately left inserted; inspection found it in 6/6 and the heating step was not started. In six, clearance was deliberately below the assembly allowance; the feeler gauge rejected 6/6 before heating. These are staged checks, not an estimate of field fault rates. No runtime penalty was measured.

Six room-temperature remove-and-reseat operations on C after opening the leaf: absolute displacement values 9, 12, 8, 15, 11, 13 µm. This is a separate manipulation test, not thermal-cycle drift and not evidence that the spring preserves calibration forever. No comparison reseating series for A, B or D was supplied. No fracture occurred among the 48 installations in the fixed constructed table.
