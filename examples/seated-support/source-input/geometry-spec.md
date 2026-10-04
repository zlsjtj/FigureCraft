# Locked specification — synthetic teaching DEMO

## Bodies and geometry

There are exactly three main rigid bodies: a rectangular base, a rectangular display panel, and a narrow stay with one integral rounded foot. Pins and axle stubs are subsidiary joint hardware, not additional moving mechanisms. The three receiving grooves are recesses in the single base; they are not blocks added on top. There is no spring, latch, slider, cable, motor, separate payload, or second stay.

Use millimetres. In the side projection, H = (0, 0) is the main hinge axis; x increases rearward and z upward. The base top datum is z = 0. The finite record uses projected hinge and foot-centre coordinates, not outer-surface coordinates. Transverse y is needed only to remove ambiguity about the stay passing beside the panel.

| Item | Locked definition |
|---|---|
| Base | Nominal rectangular body: x from −10 to 130, y from −40 to 40, z from −8 to 0; total length 140, width 80, thickness 8 |
| Panel | Nominal rectangular plate, hinge-to-top reference length 120; width 64 centred on y = 0; nominal thickness 3 |
| H | Permanent base–panel revolute joint; axis parallel to y, side-projection centre (0, 0) |
| P | Permanent panel–stay revolute joint; axis parallel to y; 60 from H along the panel's nominal length direction |
| Stay | One narrow strip, nominal transverse width 6 and side-view thickness 2; distance from P to rounded-foot centre Q is 70 |
| Lateral position | Stay centre plane y = −36; panel side edge y = −32. A short panel-side axle stub reaches the stay plane. This keeps the stay beside the solid panel |
| Foot | Integral cylindrical rounded end of the stay, axis parallel to y, radius 2, transverse length 6; centre Q |
| Grooves | Exactly three upward-open semicylindrical recesses; centres S1 = (50, 0), S2 = (75, 0), S3 = (100, 0) in side projection; each radius 2 and y extent −40 to −32 |

The foot is seated with its centre at one groove centre. Only one groove can contact the foot at a time. Contact is unilateral and releasable upward; it is not a permanent revolute joint to the base. Equal nominal radii define idealized contact, not a specified manufacturing fit. Local clearance relief at H and pin mounting details are omitted. Nominal plate and strip thicknesses identify the objects; the analytic model uses reference axes and assumes adequate local joint clearances. No production tolerances or fabrication claim are implied.

## States and operation

The complete finite domain contains three seated configurations S1–S3 and one illustrative released configuration R. S1–S3 have one active foot–groove contact and two permanent revolute connections. R has zero foot–groove contacts and the same two permanent revolute connections. The panel is held externally during release and reseating. R is not self-supporting, is not a fourth groove, and does not specify an entire motion trajectory. An operator supports the panel, lifts the foot clear, changes the angle, and seats the same foot in one other groove.

In a seated configuration with groove distance d, define theta as the acute panel angle above the positive x direction. Use the positive-height branch:

`cos(theta) = (60^2 + d^2 - 70^2) / (2 * 60 * d)`

`P = (60*cos(theta), 60*sin(theta))`

`Q = (d, 0)`

`T = (120*cos(theta), 120*sin(theta))`

T is the panel's top reference point. These equations fix the quantities in the record; x(T) is the panel top's horizontal projection, not the base length or measured occupied desk area.

For R, theta = 90 degrees, P = (0, 60), T = (0, 120), and the stay from P toward Q is directed 30 degrees below positive x. Consequently Q = (70*cos(30 degrees), 25). The lowest point of its radius-2 rounded foot is at z = 23, clear of the base. This held pose was chosen only to make a completely released configuration explicit.

## Record scope

Every value is synthetic or analytic; measured observations = 0, physical experiments = 0. All four declared cases appear in `finite-record.csv`; there is no sampling, repetition, omitted failure, uncertainty estimate, or performance ranking. Nothing in this package establishes holding load, practical stability, fatigue life, user preference, readability, or novelty.
