# Scoped mutmut feasibility pilot — 2026-09-24

## Decision

mutmut works with this project's Python 3.13/pytest environment when its isolated test tree includes the required imports and fixtures. Keep mutation testing as a **focused, opt-in test-improvement tool**, not a whole-repository mandatory gate or a claim that all invalid states are impossible. The pilot did not add mutmut to `pyproject.toml` or `uv.lock`.

Hypothesis was already a project dependency; property-based tests and mutation tests answer different questions. Hypothesis supplies generated inputs/sequences. mutmut deliberately changes implementation behavior to ask whether the selected tests notice.

## Reproducible execution

Temporary experiment PR #16 used source head `5e4edbf2a06df0596edc615b82cea637246c76eb`. [Run 36054834830](https://github.com/utof/eeg_ads1299_lab/actions/runs/36054834830), job `107819070184`, completed successfully. The [retained artifact](https://github.com/utof/eeg_ads1299_lab/actions/runs/36054834830/artifacts/10832908288) contains the exact source identity, experiment configuration, hash-locked dependency resolution, installed versions, baseline log, mutation log and result summary. Artifact archive SHA-256: `b05458a326b4fb85aaba2995f1cd8347910bba5705150a8a523c5e4c3bbc7d80c5d`.

Environment: Ubuntu runner, Python 3.13, uv 0.12.18, mutmut **3.8.0**. Existing project dependencies were exported from the committed lock; mutmut and its additional dependencies were resolved into a separate retained hash-locked requirements file and installed in `.venv-mutation`. The experiment restored its temporary working-tree configuration afterward. Its workflow uses only a read-only repository token and is not intended for merging into the product branch.

Target and focused tests:

```toml
[tool.mutmut]
source_paths = ["lab/"]
only_mutate = ["lab/validation.py"]
also_copy = ["run_lab.py", "tools/", "hardware/", "firmware/", "configs/"]
pytest_add_cli_args_test_selection = [
  "tests/test_input_boundaries.py",
  "tests/test_adc.py",
  "tests/test_extended.py",
]
```

The `also_copy` files are needed by imports and fixture lookups in this existing test selection; they are not additional mutation targets. No Pyrefly mutation filter, source exclusions for surviving mutants, or minimum mutation-score threshold was introduced.

## Observed result

| Measurement | Result |
|---|---:|
| Focused unmodified baseline tests | 31 passed |
| Mutated-tree baseline and forced-failure sanity checks | Passed |
| Generated mutants | 292 |
| Tested mutants | 267 |
| Killed by the selected tests | 207 |
| Survived the selected tests | 60 |
| No associated tests in this selection | 25 |
| Timeouts / suspicious / skipped / segfault statuses | 0 / 0 / 0 / 0 |
| Shell-recorded elapsed run time | 518 seconds |
| mutmut process exit code | 0 |

The command was wrapped in a nominal `timeout 420`, but the recorded elapsed time was **518 seconds**. Therefore this run does not establish a strict seven-minute wall-clock bound. Future recurring integration must verify process-group/termination behavior rather than claiming the nominal limit was enforced. The overall workflow also had a 15-minute job timeout.

A surviving mutant is **not automatically a defect**: equivalent behavior, changed non-contractual error wording, deliberately narrow test selection, or a missing assertion can all explain survival. The 25 no-test mutants are untested by this selection, not proof that the complete project suite has no relevant tests. The final report does not claim a repository-wide mutation score or that 60 real bugs were found. Survivor diffs were not individually classified in this feasibility run.

## Failed setup attempts are not mutation evidence

The first attempt, [run 36053525217](https://github.com/utof/eeg_ads1299_lab/actions/runs/36053525217), passed the 31-test external baseline but selected no matching module under a conflicting CLI filter; it exited 1 after 8 seconds. The second, [run 36054432638](https://github.com/utof/eeg_ads1299_lab/actions/runs/36054432638), passed the same external baseline but failed test-statistics collection because the isolated tree lacked required repository imports; it exited 1 after 19 seconds. Neither attempt executed a usable mutation study. Removing the conflicting filter and adding explicit copied dependencies produced the successful third result above.

## Smallest worthwhile follow-up

Retain this exact configuration as a documented starting point. In a dedicated test-only change, inspect a handful of survivors around finite-number rejection, boundary comparisons and type validation. Add assertions for meaningful behavioral survivors, rerun those mutants and the full ordinary suite, and distinguish equivalent/error-message-only survivors explicitly. Only then decide whether a pinned optional dependency group and a manually triggered CI job are worth maintaining.

Do not mutate every numerical/native workflow on every PR, adopt a universal 100% target, apply mutants to an uncommitted source tree, or treat a mutation-testing pass as evidence of circuit safety. No hardware, firmware, physical model or safety gate was changed by this experiment.
