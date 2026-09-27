# Dated Murata evidence, not a second BOM

Read `../../REV_A_CAPACITOR_EVIDENCE.md`. `source_record.json` retains selected
factual fields from five exact-core rows in Murata's public catalog, the official
status legend, exact technical-PDF identities and capture receipts. The English,
Japanese and Chinese status columns are retained; `channel_code=jp` is not a
worldwide inventory claim. The current BOM remains the component source of truth.

Only core-to-current-D-suffix matches are established. No generic suffix-removal
or replacement-equivalence API is introduced. Body thickness maxima in the CSV
are separate from the nominal/tolerance values visually read from the PDFs.

This historical snapshot is tested offline for consistency, not polled in CI.
Retain it when later component decisions supersede it. Manufacturer technical
exports contain typical information, not approved assembly or a guaranteed
minimum effective capacitance. No PCN/date or replacement was established.

The complete catalog, internal coefficients and JavaScript are not redistributed.
The conversation package retains the five original technical PDFs, measurement
conditions, status images and capture hashes for review. CI success is not a
source-authenticity proof or permission to use hardware.
