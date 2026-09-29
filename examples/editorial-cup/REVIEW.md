# Cup DEMO: delivered figure and editorial decision

Chosen output: `final/figure.svg`, `final/figure.pdf`, `final/figure.png` (160 × 87 mm; 300 dpi PNG: 1890 × 1028 px). The prose, caption and alternative text are in `text.md`.

The aim was to make one relationship immediately visible: **a central cylindrical post joins the closed cup base while remaining clear of the wall and below the rim**. This is a fictional structural example, not a research result. No physical dimensions, liquid, load, flow, heat transfer or performance have been introduced.

## Actual alternatives and one refinement

- `first_cutaway/` is the actual first complete drawing. It shows the cup and post through an omitted front half-wall. The round post top, continuous inner wall and exposed base support a direct spatial reading. The first render exposed a redundant back-floor arc and an overly prominent support plate; these faults remain in the preserved files.
- `second_section/` is a genuinely different complete axial-section composition at exactly the same physical size. It makes wall thickness and the post/base junction particularly explicit. Its rectangular section of the post requires the reader to recover the cylindrical form from the text, and it offers less natural spatial context.
- `final/` is the selected cutaway after the **only self-review repair**. The visible floor now occludes the spurious back outside edge, leaving one inner wall/floor junction. A smaller, lighter support plate gives the cup and post more visual priority. The base label now identifies the exposed base thickness, and the support label sits outside the plate. The complete floor and central post stay intact.

The selected representation preserves the section candidate's visible closed-base connection while retaining the cylindrical form. It is a schematic vector illustration with controlled tonal shading (D1), not a physical renderer or a measured CAD model. The support plate silhouette, proportions and colours are explanatory drawing choices, not supplied measurements or material properties. No old figure, report or external reference image was inspected.

## Review actually performed

The generating Codex agent viewed both full candidates, then the final normal-colour, greyscale and deuteranopia-simulation PNGs, including a 96 dpi placement-sized preview. In these views, the three entities remain separable, the post/base junction is visible, the post stays below the rim, the surrounding clearance remains visible, and the leaders do not cross any labels. There is no displaced or duplicated cup part. The curve cleanup removes the apparent extra rim at the floor without adding another layer.

Six short text nodes remain: five 10 pt object labels and the 9 pt `Cutaway view` qualifier. No numerical scale or experimental data are shown. The file checks verified a one-page PDF, physical size, text extraction, SVG XML, label bounds and zero embedded raster images. `final/technical_check.json` is the local narrow file check; it is not a scientific or visual approval.

The FigureCraft `audit_svg_labels.py` result is **REVIEW_REQUIRED**, retained in `final/label_audit.json`. It reports the gradient definitions, two curved boundary paths, and generic possible later-paint coverage of labels as outside its automated scope. It reports no measured text/straight-leader collision or sub-9 pt text. The displayed PDF-derived raster was visually checked for these interactions; the audit result has not been relabelled PASS. Native SVG editor rendering, real print output and cross-platform font substitution have not been independently tested. The saved comparison HTML embeds the actual SVGs for further inspection.

This is the generating agent's self-review, not an independent quality judgment, real-reader study or author acceptance. A parent agent may perform a separate review. No Nature-level quality claim or journal acceptance is made.

## Sources, hashes and portability

`loaded_sources.json` records the skill/input snapshots before figure implementation. For the first-read SKILL documents these are pre-generation snapshots, not a claim that hashing and the very first text read were atomic. Every render writes `load_record.json` **before drawing**, including the exact executing source hash, input hash, font hashes, command and UTC time. `draw_cup_first.py` preserves the first source; `draw_cup.py` is the final source. `audit_code_hash_before_run.json` records the audit code before execution.

The drawing source imports no PaperCraft/FigureCraft runtime and can be moved with `input.md`. Required external dependencies are Python, reportlab, pypdf, Pillow, numpy, Arial font files and Poppler `pdftoppm`; paths are arguments, fonts are not redistributed. `portable-check/` is a copied-source reconstruction from another working directory, not another natural-language generation trial. Its result is in `portability.json`.

Editable scope: all SVG surfaces are independent paths with stable IDs and `data-entity` attributes; shading uses editable SVG gradient stops; labels remain plain SVG text. Geometry, palette, placement, leader routing and fonts can be changed in the source. PDF preserves vector surfaces and embeds font subsets, although PDF editor ergonomics vary. PNG is a flattened export. Changing geometry after delivery requires rechecking the stated structural relations.
