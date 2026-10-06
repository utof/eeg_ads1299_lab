# Publishing work: separate the source mover from the reviewer

This note records observed methods, not a grant of permissions or a script to
execute automatically. First read live main/PR heads and the current handoff.
Do not reconstruct already-published source because a chat turn failed.

## Fresh-agent decision path (start here)

1. Read `AGENTS.md`, current `LLM_HANDOFF.md`, live main and open PRs. Inspect
   surviving branches/immutable source receipts before reconstructing anything.
2. Discover actual GitHub schemas, not names remembered from another turn.
   Connector sessions use `api_tool.list_resources(paths=["GitHub"], query=...)`:
   useful keywords are `fetch`, `create`, `update_ref`, `review_thread`, `merge`.
   Call the returned namespaced action. Do not guess unsupported arguments.
3. For ordinary text changes, `create_file`/`update_file` use actual content;
   `update_file` requires the current blob SHA. For a multi-file snapshot use
   `create_blob` -> `create_tree(base_tree_sha=...)` -> `create_commit` ->
   non-force `update_ref`. Compare returned blob/tree hashes to local Git.
   Commit metadata may change IDs even if every intermediate tree is identical.
4. Existing local Git history can instead be imported/pushed by an available
   normal authenticated Git publisher. Inspect the recorded PR77/PR81 publisher
   examples below before telling the user to set up a Codex editing environment.
   Do not hand-transcribe a large PCB or repeatedly copy large base64 streams.
5. Distinguish unavailable tooling/network from an explicit denial. Stop a
   denied operation, never bypass it through another API/service or extra
   permissions. An isolated publisher needs its own legitimate authorization;
   historical success is not permission to execute a workflow automatically.
6. Verify the actual remote feature head AND complete tree. Then request
   `@codex review` on that head and inspect ordinary CI, every original review
   thread and fresh findings. Merge through the guarded PR action only after
   acceptance, preserving history; read back main/tree. A transport job, review
   summary, old green run or successful local suite alone is not this sequence.

Root `AGENTS.md`, the README's opening table and `DEVELOPMENT.md` point here.
Do not depend on conversation memory. Record success/failure with exact action,
branch, SHA/tree and scope; retire stale handoff instructions after merging.

## Resuming an interrupted turn

A missing final answer does not prove the work failed. Read live main, open PRs
AND recently closed/merged PRs, then compare their HEAD/tree and current handoff.
Check any surviving local worktree before editing it. Preserve unrelated edits.
PR82 is a concrete example: the failed chat had already merged both S1 and the
publication instructions. The next agent verified that merge and proceeded to
S2 instead of recreating either deliverable.

Do not repeat completed work, a source upload or a blocked capability probe.
A transport archive is not active code; a completed task is not a clean review;
a green old HEAD is not verification of a new tree. Carry forward only claims
whose source and run actually match. Update the live handoff, not historical
verification receipts, when the next bounded task changes. The entrypoint checks
in `tests/test_agent_entrypoints.py` keep this guide discoverable; they test links
and instructions, not whether a future agent will reason correctly.

For a small Python/documentation change, use the available Git object actions
with actual UTF-8 bytes and compare each returned blob/intermediate tree against
local Git. Prefer that over moving a binary history archive solely for a few
text files. The original fail-first order and source trees can be retained even
when the API assigns new commit metadata; disclose the old/new SHA mapping.
Do not infer a local-file upload exists from similarly named search results.

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
