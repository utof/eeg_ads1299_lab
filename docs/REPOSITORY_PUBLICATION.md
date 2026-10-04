# Publishing work: separate the source mover from the reviewer

This note records observed methods, not a grant of permissions or a script to
execute automatically. First read live main/PR heads and the current handoff.
Do not reconstruct already-published source because a chat turn failed.

## Three different capabilities

1. **Review:** `@codex review` worked in PR79 and PR81. Review completion does not
   mean a patch was applied or the latest hardware is qualified.
2. **Editing task:** non-review Codex publication/import requests in PR80 and81
   returned a repository-environment prerequisite. Do not keep retrying the same
   request or infer that all GitHub writes or reviews are unavailable.
3. **Publication:** normal authenticated Git can import a verified bundle and
   push without force. When available, GitHub object actions can also create
   blobs/trees/commits and advance a branch. Inspect the actual available action
   schemas; one missing or rejected action is not proof that every write is absent.

For large authored files, a content-string API is not the same as a local-file
upload or Git-bundle import. Never substitute a file path for file bytes unless
the action explicitly accepts it. Check returned blob/tree hashes. Tree equality
preserves source; recreated commit metadata changes commit IDs and must be disclosed.

## Observed authorized history publication

PR77 publication run37009058604 used an isolated GitHub Actions publisher, with
Codex review requested separately. PR81 import run37204919737 used the same
bounded pattern when its workflow write was accepted: check immutable source-data
files and the complete bundle digest; verify prerequisite, exact head/tree and
changed-file scope; import without running project scripts; publish only a named
non-main branch; then clone that branch independently and check it again.

PR81 preserved all three original R1 commits through107d72c, then used a normal
non-force PR update with a merge commit to retain the documentation sibling too.
The workbench workflow and encoded recovery files are not in the product tree.
Tests run separately through the ordinary project CI, not as arbitrary proposed
code in a write-enabled publisher. A GITHUB_TOKEN-originated push may not start
all desired CI automatically: read actual runs after the connector's PR update,
and never infer checks from the successful source-transfer job.

A future publication must have its own authorization and source identities.
These historical one-shot jobs are fixed to old inputs: do not rerun them for
new work, change account permissions, weaken hash/scope checks, fetch credentials,
force-update branches, or use an alternate route after an operation is denied.
An unavailable normal path is a specific blocker to report, not an excuse to
reroute copper or repeatedly upload identical archives.

## Completion contract

Confirm the remote engineering tree, not just a staging note or transport branch.
Reconcile concurrent documentation without losing history. Run exact-head CI,
inspect each original review thread and any new findings, then merge only when
accepted. Preserve small durable receipts and current next-step instructions in
the repository. Distinguish local/hosted checks, source review and physical tests.
No publication or merge changes fabrication, purchasing, power or body-use gates.
