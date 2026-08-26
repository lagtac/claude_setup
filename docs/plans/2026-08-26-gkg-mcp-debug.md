# gkg MCP debug report — 2026-08-26

## Symptom

gkg MCP tools return nothing useful in `claude-setup`. `repo_map` failed outright with
`Project not found in workspace manager`.

## Verdict

The server is healthy. Two separate causes, neither of them a bug in the MCP transport:

1. `claude-setup` had never been indexed (fixed today).
2. **gkg 0.25.0 parses neither PHP nor Vue SFCs.** The Laravel projects have indexes covering
   only their plain `.ts`/`.js` files, so gkg answers there are silently incomplete rather than
   erroring. 0.25.0 is the newest upstream tag (2026-02-26), so there is no upgrade that fixes
   this.

## Evidence

### Server health
- `gkg 0.25.0`, pid 2360, listening on 127.0.0.1:27495 (`~/.gkg/gkg.lock`).
- MCP config is a plain HTTP entry in `~/.claude.json` → `http://127.0.0.1:27495/mcp`. Correct.
- `list_projects` responds; `form-filler` reindexed successfully at 14:23 today.
- The 549 `error` hits in `~/.gkg/logs/logs.log` are all the substring `0 errors` in progress
  lines. There are no real errors in the log.

### Cause 1 — project never indexed
`~/.gkg/gkg_manifest.json` held 4 workspace folders; `claude-setup` was not one of them, and
the string `claude-setup` appeared nowhere in the log before today. Indexing it produced:

```
Starting analysis of 0 file results for repository 'claude-setup'
Schema Stats: 0 nodes, 0 relationships
Final results: NaN% complete - 0 processed, 0 skipped, 0 errors
```

The error is gone, but the graph is empty — this repo is 45 `.md`, 3 `.json`, 1 `.sh`, and gkg
indexes none of those. gkg will never be useful here.

### Cause 2 — PHP and Vue are not indexed
| Project | Files in repo | Files gkg processed | Nodes |
|---|---|---|---|
| diagoradisa-ml | 124 `.py` | 121 | 2850 |
| form-filler | 46 `.js` | 43 | 429 |
| diagoradisa-palmist | 107 `.php`, 17 `.ts`/`.js` | **17** | 102 |
| diagoradisa-annotator | 265 `.php`, 127 `.ts`/`.js`, 31 `.vue` | **132** | 1213 |
| claude-setup | 45 `.md` | 0 | 0 |

Re-indexing palmist today against the current server reproduced it exactly: 17 processed, the
same 17 as its `.ts` + `.js` count, 102 nodes. `repo_map` on `palmist/app` returns directory
names and `No indexed definitions found`; `repo_map` on `palmist/resources/js` returns full
definitions. Language analysis modules found in the binary: C#, Java, Kotlin, Python, Ruby,
Rust (+ JS/TS, demonstrated empirically). No PHP.

`.vue` is excluded as well: annotator's 132 processed files line up with its 127 tracked
`.ts`/`.js`, not with the 158 that would include Vue. `repo_map` on `App.vue` and
`AnnotationList.vue` by exact path returns `No indexed definitions found`. So in the annotator,
gkg sees the TypeScript modules and stores but none of the 31 components.

This is the dangerous failure mode: the tool answers, and the answer is a confident subset.

### Cause 3 (mechanical) — the CLI refuses to run while the server is up
```
$ gkg index /home/dchris/projects/claude-setup
ERROR Error: gkg server is running on port 27495. Stop it before running this command.
```
Index through the running server instead — the web UI at http://127.0.0.1:27495, or:
```
curl -X POST http://127.0.0.1:27495/api/workspace/index \
  -H 'Content-Type: application/json' \
  -d '{"workspace_folder_path":"/abs/path/to/repo"}'
```
The MCP `index_project` tool only re-indexes projects already in the manifest; it cannot add one.

## Actions taken
- Indexed `/home/dchris/projects/claude-setup` (manifest entry created, graph empty as expected).
- Re-indexed `diagoradisa-palmist` as a diagnostic (unchanged: 17 files, 102 nodes).

## Recommendations (not applied)

1. **`GLOBAL-CLAUDE.md:120` (Mandatory Exploration step 0)** — edit the repo file, not the
   `~/.claude/CLAUDE.md` symlink that points at it. Line 53's review rule ("map changed symbols
   with `mcp__gkg__repo_map` … grep only when gkg can't answer") needs the same caveat. It is
   only sound for `diagoradisa-ml` (Python) and `form-filler` (JS). Suggest making it
   conditional: use gkg for Python and plain `.ts`/`.js`; fall back to Glob/Grep for PHP, Vue
   and doc/config repos. As written, following the instruction on a Laravel repo yields a caller
   list missing every PHP caller and every Vue component — which the Reference Sweep rule then
   treats as ground truth. `GLOBAL-rules/php.md` mentions gkg nowhere; that is the natural home
   for the PHP-specific carve-out.
2. **Stale indexes:** annotator last indexed 2026-06-19, ml 2026-06-16, palmist 2026-05-20.
   Wrong-not-erroring. Re-index or drop them.
3. **Worktrees:** `form-filler/.claude/worktrees/async-fill` is registered as its own project.
   The mandatory-worktree workflow lands in an unindexed path on every new branch; indexing the
   main checkout does not cover the next worktree.
4. **Vendor noise:** eight `palmist/vendor/symfony/*` packages are registered as separate
   projects (7 of the 8 index to 0 nodes). `gkg remove` can drop them; harmless otherwise.

## The form-filler symptom (reported after the first pass)

Same as Cause 1 — the project was not in the graph at the time of the call. From the session
transcripts in `~/.claude/projects/-home-dchris-projects-form-filler/`, every gkg call that
ever failed there:

| When | Call | Error |
|---|---|---|
| 2026-08-19 11:22 | `repo_map` on `form-filler/src` | `Project not found in workspace manager` |
| 2026-08-21 06:04 | `get_references` ×4 | `File not found in workspace manager` |

form-filler was first indexed **2026-08-21 06:14:43** — ten minutes after the last of those
failures. Two of the four `get_references` calls targeted
`.claude/worktrees/async-fill/src/content/combobox.js`, which was registered as its own project
by that same 06:14 index run and not before. Nothing was wrong with the server or the MCP
transport on either date; there was simply no index.

It works now: `list_projects` and `search_codebase_definitions` both succeeded at 14:21 today.

**But the same session shows the staleness failure live.** At 14:22 gkg reported `confirmSave`
at `popup.js:585` while grep put it at 603 — the index was 5 days old. The server log then shows
`graph_initial` / `graph_stats` requests at 14:22–14:23 (the web UI) followed by a manual
re-index job. There is no auto-reindex on file change: form-filler's index sat untouched from
08-21 to 08-26 through active development. Recommendation 2 is not hypothetical.
