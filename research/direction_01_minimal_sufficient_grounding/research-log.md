# Direction 01 Research Log

Append-only timeline. Commands and claims are recorded with validation state; timestamps use Asia/Shanghai (`+08:00`).

| # | Time | Type | Summary |
|---:|---|---|---|
| 1 | 2026-08-14 02:43:37 | bootstrap | User supplied and approved the full long-running goal, operational scope, LOCKED_CORE, Git workflow and completion criteria. Long-term Goal registered. |
| 2 | 2026-08-14 02:44 | bootstrap | Read `AGENTS.md` and selected autoresearch, research-lit, planning, TDD, incremental implementation, code review and documentation disciplines. |
| 3 | 2026-08-14 02:45 | failure | Heartbeat create call used lowercase `active` and was rejected by the tool enum. No automation was created. Retried with `ACTIVE`; automation `memoryrush-direction-1-autoresearch` created and verified. |
| 4 | 2026-08-14 02:46 | protection | Recorded `main`, HEAD `9676df6`, four modified task files, 28 untracked project files, ignored manifest, diff stats, disk and remotes. No non-Git file >=25 MB was found. |
| 5 | 2026-08-14 02:47 | failure | First secret-scan script failed because PowerShell constructed nested path arrays. It made no filesystem changes. Flattened list and reran successfully. |
| 6 | 2026-08-14 02:48 | protection | Scanned 54 committable files for private-key blocks and common AWS/GitHub/OpenAI/generic-secret assignment patterns; zero potential hits. `.env.example` was a filename-only hit and is an explicit placeholder. |
| 7 | 2026-08-14 02:48 | protection | Created `codex/direction1-autoresearch`; checkpoint commit `8499f5f` preserves exactly the pre-research dirty state and explicitly attributes it to the user. Pushed branch to origin. Ignored `.venv`, caches and processed artifacts remain local. |
| 8 | 2026-08-14 02:50 | phase-0 | Began source-of-truth, code, test, artifact and environment baseline audits. Spawned independent read-only literature, code and artifact/environment audit agents. |
| 9 | 2026-08-14 02:52 | protocol | Committed pilot protocol `08d9387` before any Direction 1 result; defined matched coverage, baselines, audits, downstream controls and kill criteria as provisional. |
| 10 | 2026-08-14 02:53 | failure | Combined push/test/smoke command was blocked before execution because it contained dynamic temporary-file deletion. Split into non-destructive operations; no push/test/smoke had run in the rejected call. |
| 11 | 2026-08-14 02:54 | phase-0 | Existing `.venv`: Python 3.14.5rc1, outside project range and missing pytest. System Python 3.8.6 is too old. Created ignored `venv/research` with Python 3.13.14 and installed pytest 8.4.2 via uv. The setup command's final `python -m pip show` failed because the uv venv omits pip; `uv pip list` verified pytest. |
| 12 | 2026-08-14 02:55 | phase-0 | Pre-change full suite: 15 passed/0.26s; compile exit 0; CLI exit 0; fake pipeline exit 0. Fake artifact SHA-256 `7b3250...cb567`, 1,292 bytes, ignored. |
| 13 | 2026-08-14 02:56 | inner-loop | `run-debug-001` reproduced current validator semantic blind spot: source says `may ... under tested configuration`, MemoryUnit says `always`, real paragraph ID causes current report to remain valid. Classified DEBUGGING because exact fixture was not frozen in the protocol commit. |
| 14 | 2026-08-14 02:57 | tdd | Contract RED run failed during collection with `ModuleNotFoundError: memoryrush.admission`. Added only provisional models/enums/total-matrix invariants. Focused 5 passed; full regression 20 passed/0.18s; compile exit 0. |

## Command ledger

| Command / operation | Purpose | Exit / status | Output or evidence |
|---|---|---:|---|
| `git status --porcelain=v2 --branch` plus diff/untracked/ignored manifests | Freeze pre-research state | 0 | Commentary tool output; summarized above |
| Content-level secret pattern scan over tracked + untracked committable files | Prevent secret checkpoint | first 1, retry 0 | 54 files, 0 potential hits |
| `git switch -c codex/direction1-autoresearch` | Isolate research | 0 | Branch created |
| `git commit ...` | Recoverable user-work checkpoint | 0 | `8499f5f` |
| `git push -u origin codex/direction1-autoresearch` | Remote recovery point | 0 | Remote branch created |
| `venv/research/Scripts/python.exe -m pytest -q` before Direction 1 code | Existing regression baseline | 0 | 15 passed in 0.26s |
| `... compileall -q memoryrush scripts app tests` | Syntax/import compilation baseline | 0 | Passed |
| `scripts/process_article.py ... --provider fake` | Existing deterministic pipeline smoke | 0 | Valid ignored artifact, hash recorded |
| Focused pytest before contracts implementation | TDD RED | 1 | Missing `memoryrush.admission` during collection |
| Focused pytest after contracts implementation | TDD GREEN | 0 | 5 passed in 0.05s |
| Full pytest after contracts implementation | Regression | 0 | 20 passed in 0.18s |
