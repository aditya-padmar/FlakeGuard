# Upstream integration and performance fixes — 2026-09-26

## Git state and preservation

Fetched `https://github.com/aditya-padmar/FlakeGuard.git`. Its default branch is `main`, at `6ad3482078a6cbe0c60ef27ba8c3d7c2283fc80d` when fetched.

The workspace was already on `integration` (`40bdf6c045d2b200370c8538b3035a9cad27abef`) with an uncommitted merge whose `MERGE_HEAD` was that exact latest `main` commit. No new merge was started over it. The existing merge had no unmerged index entries; 149 of 150 incoming changed files already matched the incoming tree, with a local resolution in `backend/harness/validate.py`. That resolution was reviewed and corrected without discarding the upstream feature work.

No commit, push, reset, clean, stash, or checkout was performed. The merge remains intentionally pending; existing staged work is retained and the new fixes remain local. The branch's HEAD has not moved.

A backup of changed/untracked files, staged and unstaged patches, and index/merge metadata was saved outside the repository:

`D:/FlakeGuard-main/_backups/pre-upstream-review-20260926-150904-86481e.zip`

Other local work changed during this task. Such files were re-read before editing, and unrelated UI additions were preserved. No session evidence logs or user data were deleted.

## Verified fixes

### Backend

- Mixed PASS/FAIL results now flag flaky tests even in the default five-run plan. Removed the impossible three-pass-plus-three-failure requirement for five runs.
- Completed requested run plans instead of declaring stability after a passing prefix. Removed repeated partial-result analysis. Correctness takes precedence over superficially faster but incomplete sampling.
- Removed invented execution histories for unsupported repositories. Non-pytest frameworks are detected but return explicit `unsupported` without claiming tests ran until their runner integration is reliable.
- Preserved framework identity, unified relative path identities across detection/classifications/fixes, returned consistent empty audit schemas, and removed unrelated sample-quarantine fallback.
- Moved blocking clone/extract, preflight, source/provider/remediation/audit work off the async request loop.
- Added bounded subprocess waits (collection 30 seconds, individual run 60 seconds, Git metadata 5 seconds), total pipeline execution deadline, upload-size/run-count validation, and bounded history.
- Removed repository-wide cache/state deletion. Each run receives a unique temporary state/report directory.
- Preserved full old/new source in patch proposals, fixed unified diff headers, and prevented patch text from being used as replacement Python source.
- Patch validation checks syntax first, scopes the requested test, uses a disposable repository copy, and stops on collection/invocation failures instead of repeating doomed attempts. Original source is not edited.

### Frontend

- Replaced repeated array scans in API adaptation with identity indexes. Regression tests enforce linear lookup work for large datasets while preserving first-match and ambiguous-audit behavior.
- Handled empty/null audit responses without crashing the dashboard.
- Added abort signals, request-generation guards, duplicate-submit protection and timer cleanup to repository-source forms.
- Kept live elapsed time in the pipeline view rather than updating the whole workspace each second. Demo state updates only on stage changes.
- Lazy-loaded landing, auth, dashboard and pipeline route modules instead of loading all routes upfront. The primary app bundle decreased from roughly 396 kB to roughly 291 kB uncompressed in the checked builds; route chunks load as needed. This is a bundle-size comparison, not a measured end-to-end latency guarantee.
- Capped beams drawing at 30 frames/second, preserving elapsed-time movement on high-refresh displays. Added deterministic redraw-budget tests.
- Paused sample playback offscreen/hidden and honored reduced-motion settings; removed state updates nested inside another state updater.
- Canceled landing-button delayed submission on unmount and validated input before animation. Duplicate submit requests are blocked synchronously.
- Retained the transparent landing hero/form directly on the background and removed the remaining hero spotlight container treatment.

## Verification

- Frontend: 56 tests pass, including lifecycle, data scaling, API signal forwarding, redraw budget, isolated timer and landing cancellation tests.
- Frontend production TypeScript/Vite build passes; configured lint passes. Configured lint is scoped to redesigned surfaces; additional assigned ingestion/API/UI files were linted during their implementation. Unused legacy pages were not comprehensively lint-cleaned.
- `npm audit`: zero reported vulnerabilities at verification.
- Combined selected backend baseline and regression suites: 171 passed in 4.91 seconds.
- Additional path-resolution/compatibility regressions were run with real process creation blocked (63 passed, 2 skipped, 9 deselected in the scoped backend check).
- Real pytest smoke, using only three authored fixtures in an OS temporary directory: two runs, three tests each, PASS counts 2 then 1, FAIL counts 1 then 2, exactly one alternating test identified as flaky. No remote repository or provider involved.
- Browser: landing loads after fresh refresh, content is directly on the beams background, sample demo reaches the dashboard after lazy route loading. No live GitHub repository analysis or OAuth flow was exercised.
- Both staged and unstaged `git diff --check` pass; no unmerged entries; HEAD/MERGE_HEAD remain unchanged.

## Remaining limits

This is a targeted, tested pass over known errors and hotspots, not a claim that every possible project issue is fixed.

- The untracked universal runner remains preserved but is not wired into live execution. Its parser/cache behavior needs separate integration work; unsupported frameworks now fail honestly instead of producing synthetic success.
- Temporary copies are filesystem isolation, not an OS/container/network sandbox. Only authorized, trusted test repositories should be executed.
- Subprocess deadlines terminate the direct process; descendant-tree termination and immediate cancellation of worker threads remain limited.
- Direct legacy classification/audit endpoints, provider retry defaults, and clone/upload retention are not comprehensively redesigned here.
- This machine uses Python 3.14 with newer installed FastAPI/Pydantic/pytest versions than `requirements.txt`; no global downgrade was performed. OpenAI/Anthropic SDKs and pytest-xdist were absent. External provider integrations were mocked and need their configured dependencies/credentials for live use.
- End-to-end execution of arbitrary GitHub repositories, real provider calls and a full external-repository test suite were deliberately not run.
