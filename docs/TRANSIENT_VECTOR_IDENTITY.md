# Transient output identity: names are part of the contract

A finite, correctly shaped table is not enough to identify a simulated signal.
The previous reader discarded the `wr_vecnames` header. Reordering VIN, EN and
VOUT could therefore give a retained power result the wrong meaning. The same
reader serves the linear BIAS and output-limiting studies.

## Existing ownership, stricter boundary

`lab.analog.run_ngspice_transient` remains the public execution/reading boundary.
Its additive `expected_vectors` argument specifies an immutable tuple of exact
names in their expected order. For example:

```python
run_ngspice_transient(
    netlist,
    output_dir,
    columns=3,
    expected_stop_s=0.02,
    expected_vectors=("v(in)", "v(en)", "v(out)"),
)
```

The existing `columns` argument remains supported; an explicit vector contract
must have the same length. Invalid names, duplicate requested names and malformed
requests are rejected before executable discovery or filesystem work. Count-only
callers can omit `expected_vectors`, but their header must still identify `time`
and have the same width as the requested data table. Whitespace between header
fields is insignificant; names and ordering are exact.

The reader uses one open descriptor for the header and numeric rows. It does not
silently reorder unexpected columns, infer intended nodes from the supplied
netlist, or read the numbers from a separately reopened pathname. Read/decoding
failures are rejected through the existing error boundary. Existing finite-value,
shape, monotonic-time and raw integration-window checks remain in force.

The power pilot's existing `_run` helper takes the vector tuple and derives the
column count. Its two fixtures declare `v(out)` or `v(in), v(en), v(out)`. The
linear BIAS study declares `v(common), v(out)`; the overload study adds `v(vm)`.
There is no new simulator wrapper, package, dependency, board-specific branch in
the generic reader, or alternative report publisher. Public facade exports and
Tach dependencies are unchanged.

These are exporter-consistency checks, not authentication of ngspice, the
netlist's internal connectivity, the vendor model, or physical signal identities.
A wrongly wired model can still emit correctly named columns. The independent
asymmetric pin-swap regression from PR #33 remains necessary. A single descriptor
also does not prevent another process from modifying the same file in place.

## Failure and evidence behavior

Mislabeled tables raise `RuntimeError` before voltages can be interpreted as
named outputs. The existing power rejection path retains their table, netlist,
initialization and log; unrelated probes still run and their manifest hashes
remain checkable. A rejected trace does not gain a `final_output_v` claim.
Completing native integration alone does not make a malformed export usable.
No voltage tolerance, numerical solver, vendor-library edit or hardware gate
changed.

## Dated local verification — 2026-09-26

The recovered source archive has the exact Git tree
`6779bf46fcd4dde1504808414970e703df7a592c`, matching upstream
`9c04dc7581ed570da64c53d2ae8b60b8a9a0e9b3` after PR #33.

The initial test-only change produced 21 intended failures: ten exposed accepted
bad headers through existing public entry points, and eleven exercised the new
argument before implementation. This includes six mislabeled vendor-report
fixtures that the previous public pilot accepted as completed. All are explicitly
software doubles, not TI execution.

The comparable available-environment suite passed 202 existing software tests on
the unmodified base and 223 after the change, including all 21 new software cases.
One installed-package CLI smoke test was excluded because locked installation was
unavailable; it failed for the same missing `lab` import from outside the checkout.
The remaining deselections are native/integration cases. Two new handwritten
native cases cover correctly ordered and reordered actual ngspice exports, but
were **not executed** here.

Retained-output replay verified 185 unique manifest-listed files from native
artifact `10893737134` (run `36204973708`) and 111 from optional TI artifact
`10892848526` (run `36205018193`). Both belong to the prior PR #33 candidate,
not this patch. All 40 saved trace tables were exercised through the public
reader with a replay-only process double. The 34 complete tables were read with
exactly unchanged numeric arrays; the six previously incomplete vendor tables
remained rejected. The original reader accepted all 34 complete-table identity
corruptions; the named reader rejected all 34. These are directed fault injections,
not a whole-project mutation-testing score or 34 new native experiments.

The local Python 3.13.5 environment had the pinned numerical packages and pytest,
but not the full locked development environment. Locked setup/check attempts
failed on unavailable downloads. Broader available-environment suite attempts
also had dependency/tooling failures and did not finish within their execution
bounds. No full-suite, coverage, Ruff, Pyrefly, complexipy or Tach pass is claimed.
No new ngspice execution, target firmware build or independent external review
was performed. This dated verification supports an **unmerged candidate**, not
release or merge approval; run the normal locked quality/native gates before
merging.

The existing TPS7A20 enable-off failure remains unresolved. In particular, these
checks do not justify smoothing or replacing the comparator equations. All
hardware, firmware, purchasing and body-connection gates are unchanged.

## Completed recovery of PR #37

The earlier subsection records the original tool-limited attempt, not current
merge status. PR #37 was merged at `d9ec94c0d2617dace65c167dfb8e22bec819c51e`
after final head `4a58993c57c764abff129b5f874f1b5b58c601ee` passed Quality
`36209863734` (Python 3.11/3.13/native), Firmware `36209863753`, and a completed
Codex review reporting no major issues. The restored locked local native gate
also passed: 527 software tests plus five subtests, 48 native tests, and
677/842 actual branches (80.40%, unchanged 71% floor). All 185 final native
manifest file hashes plus four firmware source and four binary hashes were
verified. No optional vendor-model rerun or physical validation is implied.

## AC companion contract (PR #38)

The AC reader had the same discarded-header gap. A real ngspice RC fixture
with `wrdata ac.txt hi hr` returned swapped complex components without rejection.
The test-first follow-up reproduced 16 intended failures and retained five passing
controls before changing the implementation. That includes 11 header/axis false
acceptances, four malformed-input exception gaps, and the native output-order
mutation. Already rejected single-row/nonfinite cases are controls, not new bugs.

`run_ngspice()` now requires the lab exporters' `frequency hr hi` header and a
finite, positive, strictly increasing frequency axis with at least two rows.
External custom exporters must use these names and the real-then-imaginary order;
this deliberately rejects arbitrary three-column files, including `real imag`
aliases. It does not silently reorder, rename or rescale supplied data.

AC and transient parsing share the existing one-descriptor implementation,
renamed `_read_wrdata_table`; only their scale and expected vectors differ.
Axis semantics stay in the respective public readers. There is no second runner,
parser module, abstraction framework, dependency, model or tolerance change.

A deterministic 40-example Hypothesis property checks that independent real and
imaginary values survive parsing. The unmutated native RC response is compared
with `1 / (1 + j*2*pi*f*R*C)`, not output generated by our solver. Seven narrowly
selected source mutations were all caught: dropping scale/vector checks,
allowing zero/repeated frequencies or nonfinite responses, swapping complex
components, and changing frequency units. This is a directed experiment, not a
whole-project mutmut score. Final locked/CI results remain attached to the exact
PR head; the test-first and focused results are not substitutes for those gates.

These checks do not prove completion of an independently requested AC sweep,
authenticate ngspice, identify circuit internals, or validate physical hardware.
The transient raw integration-window checks remain required and unchanged.
