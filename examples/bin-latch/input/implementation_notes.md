# Implementation notebook fragments

**DEMO FICTION — preset constructed design and outcomes; no physical prototypes, real tests, numerical simulation, or real literature search.**

These fragments supplement the loose draft. Their order is the notebook order, not a requested paper structure. Configuration letters are neutral identifiers. No candidate paper contribution has been selected here.

## Fragment 07: common hardware boundary

- Object: one upper corner of a small returnable bin. Two wall panels meet at 90 degrees. The housing remains fixed to one wall; the other wall ends in a detachable flat tab.
- The removable tab moves along +x into a receiving channel. Outward separation acts along -x. The tab plane is x-z, its 2.8 mm thickness is along y, and +z points up toward the bin rim.
- Common external housing envelope: 28 mm in x, 22 mm in y, 18 mm in z. These are the hardware envelope dimensions, not an illustration crop.
- Same nominal wall-tab stock and hardware envelope in all four variants. Internal pockets and tab locking openings differ. Do not describe a single identical housing used unchanged for all variants.
- A, C, and D engage a rectangular window through the tab thickness, nominally 8 mm along x and 6 mm along z. B uses a 2.2 mm diameter hole instead. The insertion depth is set by a common external shoulder at x = 20 mm.
- All fictional hardware is machined stock. Housing/key/shoe/sled are POM polymer; wall tab is polypropylene. B's pin and retaining loop are stainless steel. No numerical modulus, yield stress, material certificate, or moulded prototype is available.

## Fragment 02: inherited practices

The base corner receiver, a stop shoulder controlling tab insertion, chamfered lead-in, and a flexible catch returning after insertion were inherited choices inside this fictional project. A is the in-project starting snap configuration; this is not a claim about the history of real products. B was retained as a mechanically distinct control because a cross-pin holds the tab without a snap tooth. A common hardware envelope, equal wall stock, separate destructive specimens, and unloaded release were also established before the D pocket revision. No external citation is attached to these practices.

## Fragment 11: dimensional record for D

- Housing guide allows shoe translation in y. The engaged tooth projects 1.0 mm in -y into the tab window. Pulling the tab in -x presses its window edge against the tooth; a rear shoe surface bears against the housing stop. The stop normal is along x.
- The shoe body is nominally 8 mm in x, 7 mm in y, and 5 mm in z, excluding its tooth and return tongue. Tooth engagement along x is 2 mm. The dimensions are geometric inputs, not FEA-derived optima.
- A return tongue is integral with the shoe and biases it in -y. It sets engagement and return; the loaded stop is the specified direct reaction surface for the tab's -x pull. No quantitative force partition between tongue and stop is known.
- A separate sled slides +z by 3.0 mm. Its straight ramp then displaces the shoe +y by 1.2 mm. The kinematic displacement ratio is 0.4; no efficiency or friction coefficient has been determined. The endpoint gives 0.2 mm nominal clearance beyond the 1.0 mm overlap.
- The shoe's contact with the stop is allowed to slide in y during unloaded release. The present geometry is not asserted to release while under tensile wall load; friction under preload was not tested.
- The sled returns when released through the shoe tongue and ramp interaction. This return is a design intention, not a measured return-time result. No extra spring or pivot pin is part of D.

## Fragment 04: control variants and a troublesome modification

A: one flexible snap key plus housing, two discrete hardware parts. Its compliant region is 18 mm long and 0.9 mm thick. Tab insertion retracts the tooth and the key springs back. The loaded tooth and the compliant key are the same piece.

B: housing, a 2.0 mm steel cross-pin, and its retaining loop, three discrete hardware parts. The loop prevents loss; it does not carry the stated outward load. The release actuator withdraws the pin along y. The 2.2 mm hole is not particle proof.

C: housing plus a thicker snap key, two parts. The flexible region is 14 mm long and 1.3 mm thick. The key uses the same 1.0 mm nominal tooth overlap as A. The constructed comparison deliberately retains this version even though release becomes difficult. C is not the final D geometry and is not to be removed as an inconvenient outlier. Its larger retention number is a pullout result, not evidence of better serviceability.

No measured beam strain or stress model exists. The relative dimensions can motivate an explanation of compliance, but cannot establish a fatigue mechanism or a polymer damage law.

## Fragment 13: excluded scratch trial and later choice

Before freezing the eight comparison cells, D0 had a 0.15 mm nominal shoe-pocket side clearance. A single deliberately positioned 0.20 mm grain prevented complete release in a qualitative scratch exercise. Its release force reached the 60 N ceiling. D0 was then changed to D: 0.45 mm nominal side clearance and a 1.2 mm wide open underside relief slot. This scratch entry is fictional like the rest of the package; it has no repetition count, retention result, or statistical status and must not be folded into the CSV.

The larger clearance permits lateral play. The design drawing's adverse-position check leaves 0.7 mm minimum tooth overlap, compared with 1.0 mm nominal. This is a deterministic geometry check, not a distribution or a measured population minimum. No grain evacuation fraction was calculated. D still has two failed final releases in the gritty comparison cell.

## Fragment 05: fixture protocol, including awkward details

- Eight comparison cells: A/B/C/D crossed with clean/grit. Each cell has 20 release fixtures and a different group of 6 destructive-pullout fixtures. All groups are independent by construction. Total: 8 x 26 = 208 fictional fixtures.
- Each fixture stays engaged for 300 triangular tensile load cycles, 20–120 N at 1 Hz. The sequence does not repeatedly detach the tab. No mechanism failed open during this prescribed constructed cycling sequence. This does not imply survival at higher loads or for more cycles.
- Grit is dry spherical glass granules, diameter 150–300 micrometres. Doses of 0.15 g occur before initial tab insertion, after cycle 100, and after cycle 200. Total dose 0.45 g per fixture. No cleaning, water, oil, mixed dust, or additional grit types.
- Final release: wall preload reduced below 2 N; one actuator attempt at 5 mm/min along intended release direction; 60 N force ceiling; 10 mm maximum travel. A/C are actuated at their release pad, B by withdrawing the pin, and D at its sled. Success is full disengagement of the locking member from the tab. No second attempt or helpful shaking.
- Peak release force median is computed over successful attempts only. The CSV's successful sample count is also its denominator for that force median. Do not assign the force ceiling to failures and call that a recorded median.
- Separate post-cycle pullout: monotonic -x tab loading at 5 mm/min until retention is lost. Report median and observed minimum/maximum across six fixtures. These are not confidence intervals or uncertainty bounds on the median.
- No randomization, blinding, hypothesis test, or preregistration actually occurred. This is a finite preset dataset for document generation, with no inferential statistics authorized.

## Fragment 16: cost and remaining defects

Complete hardware masses exclude the wall tab but include the housing and all variant-specific retention parts: A 8.4 g, B 10.9 g, C 9.2 g, D 12.6 g. D therefore weighs 50% more than A. A and C use two discrete parts; B and D use three. An integral tongue is not an additional discrete part.

D adds a separate sliding piece, an extra internal pocket operation, and an alignment step at assembly. No price, manufacturing yield, assembly duration, recycled content, or environmental impact was measured. The mass penalty is available quantitatively; the rest are qualitative costs only.

Constructed terminal pullout observations: A's flexible key bends out of engagement; B loses retention when its polymer tab hole elongates; C tears the tab-window edge; D fractures the housing stop lip. These descriptions are coarse prescribed observations without photographs or independent analysis. No subcritical damage history should be invented from them.

The housing is open at the underside slot. It is not sealed, waterproof, hygienically qualified, child resistant, or certified. Impact, temperature, solvents, long-term creep, repeated disassembly, reverse loads, and release under cargo preload remain untested. Grit success is 18/20 for D, not complete immunity.
