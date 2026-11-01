# Review coverage by path

Reviews are tracked by **path**: an end-to-end chain through hardware and
software (for example "ADC data to saved file"), not by file. One path crosses
many files, nets and functions; a file can belong to several paths.

## Layout

    docs/reviews/
      README.md          this protocol and the path index
      paths/<id>.md      one file per path: scope, findings, append-only log

One file per path lets parallel reviewers work without editing the same file.
Status lives only in each path's frontmatter, so there is no second index to
drift. Print the current table with:

    grep -H '^status:\|^reviewed_at:\|^stage:' docs/reviews/paths/*.md

## Paths

| id | Chain |
|---|---|
| [power-on](paths/power-on.md) | J105 5 V -> regulators -> supervisors -> C2 interlock -> firmware gate -> ADC start |
| [data-out](paths/data-out.md) | ADC DOUT -> series R -> connectors -> level shift -> ESP32 SPI -> packet -> serial -> decode -> saved file |
| [board-wiring](paths/board-wiring.md) | Every inter-board/module connector, tail and cable pin map |
| [design-to-factory](paths/design-to-factory.md) | Schematic <-> BOM <-> PCB <-> fabrication outputs and release marking |
| [safety-stops](paths/safety-stops.md) | STOP contact, C2 latch/interlock, firmware guards and their tests |
| [check-integrity](paths/check-integrity.md) | Whether `tools.check`, validators and tests fail when something breaks |
| [analog-quality](paths/analog-quality.md) | Input network, BIAS, reference, analog models/SPICE versus datasheets |
| [mechanical-fit](paths/mechanical-fit.md) | K2 carrier, supports, board thickness, connector/cable fit |

Add a path only when a real chain is not covered by these; do not split for tidiness.

## Status and staleness

- `never`: no review yet. `partial`: some of the chain reviewed; see "Not yet
  covered". `reviewed`: the whole chain reviewed against primary evidence.
- `reviewed_at` is the commit the review read. A path is **stale** when any
  `scope` entry changed since then (working tree included):

      git diff --stat <reviewed_at> -- <scope entries>

  Stale is computed, never written. File-level scope over-triggers; if the
  change does not touch the chain, record "re-checked, unaffected" in the log
  and move `reviewed_at`.
- `stage` is the earliest stage a defect on this path blocks: `before-fab`,
  `before-power`, or `later`.

## Running a review session

1. Pick a path: `never` or stale first, earlier `stage` first.
2. Read its file: scope, open findings, "Not yet covered".
3. Discover the chain with codebase-memory-mcp (`trace_path`, `query_graph`);
   read KiCad/JSON/datasheets directly. Check against primary evidence
   (datasheet section, board file, manufacturer pin table), not repo prose.
4. Confirm every finding against actual code/data before recording it.
   Unconfirmed items go in as `suspected` with what would confirm them.
5. Update the path file: new findings, "Not yet covered", one appended log
   entry, then `status`, `reviewed_at`, `reviewed_on`. Extend `scope` if the
   chain reached files not listed.
6. Mirror findings that block fabrication or power into the roadmap's
   current todo (`docs/REV_A_COMPLETION_ROADMAP.md`). Fixes still need a
   failing-first test per `AGENTS.md`.

Finding IDs are `<CODE>-NN` per path (codes in each frontmatter). Finding
status: `open`, `fixed <commit>`, `rejected: <reason>`, `suspected`.
Record durable summaries with `file:line` at `reviewed_at`; do not paste raw
reviewer transcripts. A review is not hardware qualification and authorizes
no fabrication, power or body use.

## Reviewer brief template

> Review path `<id>` of the ADS1299 repo. Read `docs/reviews/README.md` and
> `docs/reviews/paths/<id>.md` first. Find CRITICAL defects only (hardware
> damage at power, wrong fabrication data, checks that cannot fail, data
> corruption). Read-only; confirm each finding against code and datasheet;
> report findings with file:line evidence, suspected items, and exactly what
> you covered and did not. Do not run the full `tools.check` locally.
