# Spec: swappable methods

**Status:** approved, 2026-10-13. Splits the global rules into a neutral core and per-method files, and splits the `my` plugin into `my` (the method) and `kit` (neutral tools).

## How to read this spec

1. `docs/plans/2026-10-12-swappable-methods-architecture.md`: the architecture brief. Its Decision is the starting point of this spec. Its forces, candidates and spike 1 are not repeated here.
2. This spec.
3. `global/CLAUDE.md` (symlinked as `~/.claude/CLAUDE.md`): the file being split. Section names below refer to its headings on 2026-10-12.
4. `global/rules/docs-layout.md` and `global/rules/plan-format.md` (symlinked under `~/.claude/rules/`): the lazy rules that get a first line.
5. `plugins/my/hooks/hooks.json`, `plugins/my/hooks/check-orphan-plans.sh`, `plugins/my/hooks/block-autorun-push.py`: the hooks that move or change.
6. `plugins/my/tests/test_block_autorun_push.py`: the test style the new tests follow.
7. `README.md`: documents every skill, command, script and the `~/bin` symlinks.
8. `.claude-plugin/marketplace.json`: gets the `kit` entry.
9. `ROADMAP.md`: the open `my:handoff` rows that may touch the same files (see Risk).

The plan is written next, at `docs/plans/2026-10-12-swappable-methods.md`.

## Goal

The user wants to try another method in one project without rewriting `~/.claude/CLAUDE.md`. A method here is a set of skills plus the always-on rules that go with them. Today the global file mixes rules that hold under any method with rules tied to superpowers and the `my` skills, so every trial means rewriting it.

Success means:

- A project picks its method with its own `.claude/settings.json` and one import line in its own `CLAUDE.md`. No global file changes.
- `~/.claude/CLAUDE.md` holds only rules that hold under any method, and names no method and no skill.
- A project that runs an outside method gets none of our method's rules, skills or hooks, and no superpowers.
- When the switch is half set, the session says so at start.
- The 21 repos that use our method today behave as before the change: ten top-level repos in `~/projects/`, the seven repos nested in `diagoradisa/` and `grispy-web-ext/` (D13), and the four repos added by D19. The tutor repo `mv3-tab-notes` also behaves as before.
- Every other folder where sessions open becomes a neutral project at the cutover, by choice (D19).

## Non-goals

- Other agent tools (Codex, Copilot through `AGENTS.md`). The `@` import, plugins and hooks are Claude Code only. The method file is plain Markdown, so an `AGENTS.md` could point to it later.
- Changing what the `my` method's rules say. Text moves; only the paragraphs listed under "Reworded text" change.
- Lowering the text loaded per session for `my` projects. It stays as today (force 9 in the brief is assumed: tokens matter somewhat).
- A setup skill for outside methods. They bring their own, as `setup-matt-pocock-skills` does.

## Decisions

Decisions D1 to D12 were made in brainstorming on 2026-10-12, on top of the brief's Decision. D13 to D18 answer the spec review (`docs/plans/2026-10-12-swappable-methods-spec-review.md`) and were approved by the user on 2026-10-13. D19 and D20 come from a sweep of the folders where sessions open, also approved on 2026-10-13. Four decisions change the brief's wording; each says so.

| # | Decision | Reason |
| --- | --- | --- |
| D1 | One spec; the plan is split into two batches, each with its own branch, reviews and squash-merge. | The parts share decisions (names, the core boundary). Batches keep each review small. |
| D2 | The neutral core holds a section only if it holds under any method and does not conflict with that method's own process. The section table below applies this test. | A core rule such as "write a Risk section" would make every trial method partly ours, so a trial would not be fair. |
| D3 | The method is named `my`. The method plugin keeps the folder `plugins/my/` and the name `my`. **Changes the brief:** the brief renamed the method's skills; now the neutral ones are renamed instead. | `my:handoff`, `my:spec-review` and the rest keep their names. About 45 references stay untouched; the neutral sweep is 46 lines by text search on 2026-10-12, most in the file that defines the name. |
| D4 | The neutral plugin is named `kit` (`plugins/kit/`). | Short to type; says "general tools", not a method. |
| D5 | Placement of every skill, agent, command, script and hook follows the "Plugins" table below. | Files that cite `docs/plans`, `superpowers:`, `global/CLAUDE.md` or another method skill go to `my`; the rest go to `kit`. |
| D6 | `tutor` becomes a method of its own, with no plugin of its own: `global/methods/tutor.md`, and its skill moves to `kit` as `kit:tutor`. The "Learning workspaces" override list is removed. | Left in the core, the list would name `my` sections, which is the coupling this work removes. In a tutor project `my` is off, so its rules never load and need no override. |
| D7 | `my` and superpowers are **off at user scope** and turned on per project. `kit` is on at user scope. | An outside method's setup does not know about superpowers, so with superpowers on by default it would join every trial and steer the model to its own skills. |
| D8 | The guard lives in `kit`, which is on everywhere, and checks both directions. **Changes the brief:** the brief put it in the method plugin. | A guard inside `my` cannot see a project where `my` is off but superpowers or a stale import is still there. |
| D9 | When the import is not approved, the guard warns and tells the model to read the method file before its first reply. | The session still runs under the method. A headless run cannot get approval, so "stop until approved" would stop every time. |
| D10 | One setup skill, `kit:setup <method> [<project path>]`, for `my` and `tutor`. **Changes the brief:** the brief had one setup skill per method. | `my` is off in a project that is not set up yet, so `/my:setup` could not run there. |
| D11 | The cutover happens in one sitting, only after every other Claude session has stopped working. No overlap period. | No doubled rule text and no window where a rule edit must be made twice. The wait is a checked step, not a promise. |
| D12 | Supervised only. No Delegation section. | The cutover waits for other sessions, edits `~/.claude/settings.json` outside the repo, commits in 21 other repos and needs 22 interactive approvals. |
| D13 | `diagoradisa/` and `grispy-web-ext/` are folders, not repos. `kit:setup my` runs in each of their seven nested repos (`diagoradisa-annotator`, `diagoradisa-meta`, `diagoradisa-ml`, `diagoradisa-palmist`, `diagoradisa-platform`, `grispy-ext`, `grispy-site`). The parent folders are left alone. | Sessions open in the nested repos, which each have a `CLAUDE.md`, and only a repo can take the setup commit. |
| D14 | `tutor.md` names four core rules as set aside in a learning workspace: Verify against ground truth, Mandatory Exploration, Reference Sweep and Simplicity Rules. | Today's "Learning workspaces" section sets them aside. Core Precedence allows an exception that names the rule, so tutor keeps today's behaviour. |
| D15 | `optimize-prompt` and `tune-claude-instructions` stay in `kit` and are reworded to pass D5's test. `optimize-prompt` saves to `docs/optimized-prompts/` instead of `docs/plans/optimized-prompts/`. `tune-claude-instructions` writes its optional report where the user says, with no `docs/plans/` default, and its `/my:summarize` and `docs/plans/` examples become neutral ones. | Both are useful under any method; only these lines tied them to ours. |
| D16 | `claude-setup`'s `.gitignore` ignores `.claude/*` except `.claude/settings.json`, instead of all of `.claude/`. | `kit:setup` must commit the switch here too, so worktrees of this repo get it. |
| D17 | Both runbooks update the plugin cache and restart before the new plugin code is used. Cutover steps 6 to 9 run from a new session. | Sessions run the cached copy in `~/.claude/plugins/cache/`, not the repo (`README.md`, "Updating"). Without this, `/kit:setup` does not exist in the session at step 6. |
| D18 | The guard treats a missing `superpowers@synced` key as on, and a missing `my@claude-setup` or `kit@claude-setup` key as off. | Superpowers comes from the account sync and is on when no settings file names it. Our marketplace plugins are on only where a settings file says so. |
| D19 | Four more repos become `my` repos: `~/projects/zitamu/real-estate-webapp`, `~/src/containers`, `~/src/cv` and `~/src/scripts`. Every other folder where a session has opened (from the `projects` keys in `~/.claude.json` on 2026-10-13: `~/`, `~/tmp`, `~/src`, `~/.claude`, `~/.dotfiles`, `~/.config/nvim`, `~/.config/mozilla`, `~/projects/containers`, `~/Documents/notes`, `~/Documents/personal`, `~/Downloads/diago-test-photos`, and the parent folders `diagoradisa/` and `grispy-web-ext/`) becomes neutral. | Chosen by the user on 2026-10-13, after a sweep of session folders. Today all of these get the full method from the global file; after D7 only a set-up repo does. |
| D20 | Worktrees that exist at the cutover are listed in the runbook. For each, the user either merges `main` into its branch after the setup commit, or starts sessions for it only at the repo root until the branch is merged. | A branch cut before the setup commit has no import line and no settings switch, so a session started inside its worktree runs with no method and no `my` plugin, and the guard sees a neutral project. On 2026-10-13 two exist: `diagoradisa-annotator/.claude/worktrees/parallel-worktree-runs` and `zitamu/real-estate-webapp/.claude/worktrees/client-review`. |

## Architecture

### Global files

`~/.claude/methods` becomes a new symlink to `global/methods/`, next to the existing `~/.claude/CLAUDE.md`, `rules` and `output-styles` links.

| File | Holds |
| --- | --- |
| `global/CLAUDE.md` (trimmed) | The neutral core. See "Section table". |
| `global/methods/my.md` (new) | Every section of today's `global/CLAUDE.md` that the section table marks **method**, in today's order, with today's wording except "Reworded text". |
| `global/methods/tutor.md` (new) | The tutor method. See "The tutor method file". |
| `global/rules/docs-layout.md` | Unchanged except a new first line after the title: "Applies only in projects whose `CLAUDE.md` imports `~/.claude/methods/my.md`. Ignore it otherwise." Also its reference to "the size table in `~/.claude/CLAUDE.md`" becomes `~/.claude/methods/my.md`. |
| `global/rules/plan-format.md` | Unchanged except the same first line. |

### Section table

Sections of today's `global/CLAUDE.md`, by heading:

| Section | Goes to | Note |
| --- | --- | --- |
| `# Instructions` bullets: `docs/plans/` path rule, `docs/reports/` rule | method | Our docs layout. |
| `# Instructions` bullets: Conventional Commits, `type(scope)` format, common types, no new dependencies | core | |
| Learning workspaces | removed | Replaced by `methods/tutor.md` (D6). |
| Superpowers Integration, with "Size the process to the change", the trigger table, Precedence, Discovery authority | method | Precedence is split; see "Reworded text". |
| Spec → Plan two-artifact flow | method | |
| No silent reinterpretation of approved decisions | method | |
| Code Review Routing, with "Before any review" | method | |
| Communication | core | |
| UI Design | method | Names the skills `design`, `frontend-design`, `artifact-diagramming`. |
| Code | core | |
| Git Workflow and all its subsections | method | Except the Conventional Commits bullets, which stay in the core from `# Instructions`. |
| Planning Standards intro paragraph | split | See "Reworded text". |
| Verify against ground truth | core | |
| Critical Thinking | core | |
| Mandatory Exploration | core | Without the sentence that ties it to superpowers discovery skills. |
| Reference Sweep | core | Reworded. |
| Simplicity Rules | core | |
| Trade-Off Analysis | method | |
| Risk Awareness | method | |
| Test Standards | method | |
| Plan Output Format | method | |
| HTTP Requests | core | |

The core gets one new heading, `## Engineering standards`, which holds Verify against ground truth, Critical Thinking, Mandatory Exploration, Reference Sweep and Simplicity Rules. The method file keeps the heading `## Planning Standards` for Trade-Off Analysis, Risk Awareness, Test Standards and Plan Output Format.

### Reworded text

Only these paragraphs change wording. The plan quotes the final text of each.

1. **Core Precedence (new).** This file and the method file a project imports are the highest authority: when plan mode, a skill or a system default conflicts, follow them. The rules in this file hold under every method. A method file may add rules. It may name an exception to a rule in this file only by naming the rule.
2. **Method Precedence (kept in `my.md`).** Today's paragraph, minus the learning-workspace exception. Its non-overridable list keeps only the method's own rules: the `docs/plans/` output path, Git Workflow, Risk and Trade-Off Analysis, and that plans include Dependencies and Risk and follow Red → Green → Refactor. It names the core's Simplicity Rules as the rule superpowers may override, as today.
3. **Planning Standards intro.** The core keeps the sentence "These standards apply to every planning workflow" and "Verify against ground truth". The method file keeps the sentences that say which parts superpowers may override and that Mandatory Exploration yields to a running superpowers discovery skill.
4. **Reference Sweep (core).** "When a plan removes …" becomes "When a change removes, renames or changes the signature of a cross-file symbol …". The rule then says to find every reference with both a symbol tool and a plain text search, and to handle every hit. The method file adds one sentence under Planning Standards: in a plan, the "Files to Modify" list is the output of this sweep.
5. **"Before step 1 in a project for the first time" (method).** Becomes: check that the project's `CLAUDE.md` has a `## Project facts` block (see "Setup skill"). If it is missing or incomplete, run `/kit:setup my`.
6. **References to the global file.** Every place that cites a method section "in `global/CLAUDE.md`" or "`~/.claude/CLAUDE.md`" cites `~/.claude/methods/my.md` instead. Sweep result on 2026-10-12: `global/rules/docs-layout.md:135`, `plugins/my/skills/status/SKILL.md:59`, `plugins/my/skills/handoff/README.md:253`. `README.md:14` and `tune-claude-instructions` describe the global file itself and stay, with `README.md` gaining a line about `global/methods/`.

### The tutor method file

`global/methods/tutor.md` holds:

- This repo is a learning workspace: the student writes the code, the agent teaches through `kit:tutor`.
- If the `tutor` output style is not active, say so once and point to `.claude/settings.local.json` with `{"outputStyle": "tutor"}`.
- A project `CLAUDE.md` gives facts (commands, stack); workflow rules from elsewhere do not apply.
- Exceptions to the core, named as Core Precedence requires (D14): Verify against ground truth, Mandatory Exploration, Reference Sweep and Simplicity Rules do not apply in a learning workspace. The rest of the core applies.
- No vacuous tests: each test the tutor writes must fail for the right reason before the student's code exists. This restates the idea of the `my` method's rule in the tutor's own words; it is not a copy of that section.

### Plugins

| Plugin | Holds |
| --- | --- |
| `my` (`plugins/my/`, unchanged name) | Skills: `handoff`, `soundness-review`, `status`, `spec-review`, `architect`, `roadmap-management`, `clean-plans`, `changelog-management`. Agents: `code-reviewer`, `spec-reviewer`, `summarizer`. Command: `summarize`. Scripts in `bin/`: `handoff-lock.py`, `handoff-state.py`, `git-fold-fixups.py`, `locked-commit.py`, `status-scan.py`. Hooks: `check-orphan-plans.sh`, the squash-merge hook, `block-autorun-push.py`. Tests for these. |
| `kit` (`plugins/kit/`, new) | Skills: `de-slop`, `md-tables`, `briefing`, `dev-reports`, `git-squasher`, `tune-claude-instructions`, `tutor`, `setup` (new). Agents: `laravel-fullstack-expert`, `oral-medicine-expert`. Commands: `commit`, `push`, `clean-gone-branches`, `laravel-debug`, `laravel-migration-check`, `optimize-prompt`. Scripts in `bin/`: `md-expand-table.py`, `md-collapse-sections.py` (both stay symlinks to `~/src/scripts/`). Hooks: the tutor SessionStart hook, `method-guard.py` (new). Tests: `test_method_guard.py`, `test_neutral_core.py`. |

`kit` gets `.claude-plugin/plugin.json` with no `version` field, as `my` has, and an entry in `.claude-plugin/marketplace.json`.

The squash-merge hook in `my` loses its "skip in a learning workspace" check, because `my` is off there.

`optimize-prompt` and `tune-claude-instructions` are reworded as D15 says, so no `kit` file cites `docs/plans/` or a `my` skill.

The `~/bin` symlinks for `md-expand-table.py` and `md-collapse-sections.py` are repointed to `plugins/kit/bin/`. The `git-fold-fixups.py` link stays.

### Switches

| Where | Value |
| --- | --- |
| `~/.claude/settings.json` (a real file, not in this repo) | `"my@claude-setup": false`, `"superpowers@synced": false`, `"kit@claude-setup": true` |
| A `my` project: `.claude/settings.json` | `"my@claude-setup": true`, `"superpowers@synced": true` |
| A `my` project: `CLAUDE.md` | A `## Project facts` block, then the line `@~/.claude/methods/my.md` |
| A tutor project: `CLAUDE.md` | The line `@~/.claude/methods/tutor.md`. No `enabledPlugins` lines: our method plugins stay off. |
| A trial project | Whatever the outside method's own setup writes. |

## Guard: `plugins/kit/hooks/method-guard.py`

A SessionStart hook in `kit`, matcher `startup|resume|clear`, timeout 10 seconds. It reads and never writes.

**Inputs:**

1. The project root: `CLAUDE_PROJECT_DIR`, else `git rev-parse --show-toplevel`, else the current directory.
2. Method imports: lines in the root's `CLAUDE.md` and `CLAUDE.local.md` that match `^@~/\.claude/methods/([a-z0-9-]+)\.md\s*$`.
3. `enabledPlugins` from `$HOME/.claude/settings.json`, `<root>/.claude/settings.json` and `<root>/.claude/settings.local.json`, merged in that order so that a later file wins per key. A key that no file names counts as on for `superpowers@synced` and as off for `my@claude-setup` and `kit@claude-setup` (D18).
4. `projects[<root>].hasClaudeMdExternalIncludesApproved` from `$HOME/.claude.json`. The key is undocumented.

The guard reads `$HOME`, never a fixed path, so tests can point it at a temporary home.

**Behaviour:**

| State | Output |
| --- | --- |
| Imports `my`; `my@claude-setup` or `superpowers@synced` is not `true` | Warning naming each missing `enabledPlugins` line and `/kit:setup my`. |
| Imports `my` or `tutor`; the approval flag is `false` or missing | Warning: the `<name>` method import is not approved, so its rules are not loaded. Read `~/.claude/methods/<name>.md` before your first reply, and ask the user to approve the import (start a new interactive session in this directory). |
| Imports something other than `my`, or nothing; `my@claude-setup` or `superpowers@synced` is `true` | Warning naming the line that turns each one off. |
| Imports two or more method files | Warning naming them. Other checks still run. |
| No import; `my` and superpowers off | Nothing. |
| An input file exists but cannot be parsed | One line, `method guard could not read <path>`, plus whatever the other inputs still allow. |

Several warnings join into one message. The guard always exits 0 and never blocks a session. It prints the hook JSON with the text in both `hookSpecificOutput.additionalContext` (for the model) and `systemMessage` (shown to the user). The text stays under 2,000 characters, far below the 10,000-character hook cap.

## Setup skill: `kit:setup <method> [<project path>]`

`<method>` is `my` or `tutor`. `<project path>` defaults to the current repo root, so one session can set up several projects in a row.

Steps for `my`:

1. **Find the facts in the repo:** commit scopes from `git log`, the test command from `package.json`, `composer.json` or a `Makefile`, whether `docs/plans/README.md` exists, whether `git remote` lists a remote, and whether `CLAUDE.md` or `CLAUDE.local.md` has a "Parallel runs" section. Ask the user only about what the repo does not show.
2. **Find copied rules:** sections of the project's `CLAUDE.md` that repeat rules now in `global/methods/my.md`. Propose removing them.
3. **Show one diff** for `CLAUDE.md` and `.claude/settings.json`. Write nothing until the user says yes. If `.claude/settings.json` exists, merge the two `enabledPlugins` keys into it and keep every other key. If `CLAUDE.md` does not exist (as in `~/src/scripts`), create it with only the block below. The block it writes:

   ```markdown
   ## Project facts

   - **Method:** my
   - **Commit scopes:** <scopes>
   - **Test command:** <command, or "none">
   - **Plans index:** <path, or "none">
   - **Remote:** <name and host, or "none">

   @~/.claude/methods/my.md
   ```

   A "Parallel runs" section, if present, stays where it is.
4. **Commit in that project's repo**, staging only the two files. If `git check-ignore` reports `.claude/settings.json` as ignored, stop before committing, show the ignore rule, and propose an exception line for `.gitignore` (as D16 does for `claude-setup`); add `.gitignore` to the commit if the user agrees. The message: `chore: switch to the my method`. If the project uses scopes for config, follow its own commit style. Other uncommitted work in that repo is left alone.
5. **Tell the user** to start a new interactive session in that directory, so Claude Code asks for the one-time import approval.

Steps for `tutor`: step 1 checks only that `docs/learning/curriculum.md` exists. Step 2 removes the old "Learning workspaces" text if the project copied it. Step 3 writes only the import line and removes any `enabledPlugins` lines that turn `my` or superpowers on. Steps 4 and 5 as above.

The skill is a prompt, so it follows the plugin rules: it does not inherit `CLAUDE.md`, and it embeds the facts schema above.

## Batches

### Batch 1: split out `kit`

Behaviour does not change. After the merge, every project works as before: `my` and superpowers are still on at user scope, and `global/CLAUDE.md` is still whole.

- Create `plugins/kit/` and its marketplace entry. `git mv` every `kit` file from the Plugins table.
- Move the tutor SessionStart hook from `plugins/my/hooks/hooks.json` to `plugins/kit/hooks/hooks.json`.
- Rename every neutral name in `global/`, `plugins/`, `README.md`, `CLAUDE.md` and the project memory folder: `my:<name>` and `/my:<name>` become `kit:<name>` and `/kit:<name>`, for the 15 names in the `kit` row. On 2026-10-12 the sweep found them in `README.md`, `global/CLAUDE.md` (the tutor lines), `global/output-styles/tutor.md`, `global/rules/docs-layout.md` (`my:briefing`), the moved files themselves, `plugins/my/skills/briefing/SKILL.md` (`my:de-slop`), `plugins/my/skills/changelog-management/SKILL.md:65` (`my:dev-reports`), and `plugins/my/skills/handoff/README.md` (`my:push`, `/my:commit`). The plan reruns the sweep and lists every hit.
- Runbook after the merge: add `"kit@claude-setup": true` to `~/.claude/settings.json`; run `claude plugin install kit@claude-setup` and `claude plugin update my@claude-setup`; restart the session; repoint the two `~/bin` md-table links. Until `my` is updated, its cached copy still carries the tutor hook, so the hook may fire twice in a learning workspace for that short time.

### Batch 2: the cutover

Everything that must land together, in one squash commit:

- `global/methods/my.md` and `global/methods/tutor.md` created, and `global/CLAUDE.md` trimmed, in the same commit, so the moved text exists in exactly one place at every commit.
- The first line in `docs-layout.md` and `plan-format.md`, and the reference changes under "Reworded text" item 6.
- `kit:setup`, `method-guard.py` and their tests. The guard waits for this batch because before the cutover it would warn in every project.
- The squash-merge hook loses its learning-workspace check.
- `.gitignore` in this repo changes as D16 says.
- `README.md` documents `global/methods/`, the `~/.claude/methods` link, `kit:setup` and the guard.

### Cutover runbook

It runs after batch 2's reviews pass, in place of a plain squash-merge.

1. **Wait for other sessions.** Repeat until both are clear: `handoff-state.py` lists no active auto run, and `pgrep -a claude` shows no `claude` process except the current session. Do not go on while either finds something.
2. Squash-merge batch 2 on `main`.
3. `ln -s /home/dchris/projects/claude-setup/global/methods ~/.claude/methods`.
4. In `~/.claude/settings.json`, set `"my@claude-setup": false` and `"superpowers@synced": false`. Back up the file first.
5. Run `claude plugin update kit@claude-setup` and `claude plugin update my@claude-setup`. End this session and start a new one in `claude-setup`; steps 6 to 9 run there (D17). The new session sees the trimmed global file. The guard prints nothing yet, because this repo has no import line until step 6 and both plugins are off at user scope. If check 2 in task 0 showed that a session cannot write into other repos, start it with `--add-dir ~/projects --add-dir ~/src`.
6. Run `/kit:setup my <path>` for each `my` repo: `claude-setup`, `grispy2-web-ext`, `irini`, `lequal`, `maritime`, `mv3-starter`, `niche-research`, `notegraph`, `notes-cli`, `webext`, and the nested repos `diagoradisa/diagoradisa-annotator`, `diagoradisa/diagoradisa-meta`, `diagoradisa/diagoradisa-ml`, `diagoradisa/diagoradisa-palmist`, `diagoradisa/diagoradisa-platform`, `grispy-web-ext/grispy-ext`, `grispy-web-ext/grispy-site`, `zitamu/real-estate-webapp`, `~/src/containers`, `~/src/cv`, `~/src/scripts` (21 repos). Then, for each repo, run `git worktree list` and handle each extra worktree as D20 says. Run `/kit:setup tutor ~/projects/mv3-tab-notes`. Four repos have unrelated uncommitted work (`lequal`, `niche-research`, `notes-cli` on 2026-10-12, `~/src/containers` on 2026-10-13); the setup stages only its own two files.
7. For each of the 22 repos, run the guard by hand with `CLAUDE_PROJECT_DIR` set to it. The only warning allowed is "import not approved".
8. The user opens each repo once in an interactive session and approves the import.
9. Step 7 again: the guard prints nothing in any of the 22 repos.

### Rollback

- `git revert` the batch 2 squash commit, and set the two switches in `~/.claude/settings.json` back to `true` (or restore the backup).
- `global/CLAUDE.md` is whole again. The project import lines then point to a file that no longer exists, which Claude Code skips without a message, so they do no harm. They can be removed later.
- Batch 1 needs no rollback to undo batch 2. On its own it is reverted the same way, plus the `~/bin` links.

## Testing

Tests follow `plugins/my/tests/test_block_autorun_push.py`: `unittest`, with each script run as a subprocess. They run with `cd plugins/kit && python3 -m unittest discover tests`, and the `my` tests with `cd plugins/my && python3 -m unittest discover tests`.

- **`plugins/kit/tests/test_method_guard.py`.** Each test builds a temporary `$HOME` with `.claude.json` and `.claude/settings.json`, and a temporary project with `CLAUDE.md` and `.claude/settings.json`. One test per row of the guard's behaviour table, asserting the exact warning text or empty output. Also: unreadable JSON, a missing approval flag, local settings overriding project settings, two imports, and exit code 0 in every case.
- **`plugins/kit/tests/test_neutral_core.py`.** Reads `global/CLAUDE.md` and fails if it contains `my:`, `superpowers:`, `docs/plans`, `docs/reports`, or any heading the section table sends to the method. It also checks that `global/methods/my.md` exists and that `docs-layout.md` and `plan-format.md` start with the "Applies only" line.
- **Text moved without loss (batch 2, one-time).** A short script lists each paragraph removed from `global/CLAUDE.md` and finds it in `methods/my.md` or `methods/tutor.md`. The paragraphs under "Reworded text" and the dropped override list are the only allowed misses, listed by name in the script. The script and its output go in the plan; the script is not kept.
- **Rename sweep (batch 1).** `git grep` for each old `my:<kit name>` in `global/`, `plugins/`, `README.md`, `CLAUDE.md`, and `grep` in the memory folder, finds nothing. Committed docs in `docs/` keep the old names. The `my` tests still pass after the move.
- **Checks before the cutover (plan, task 0):**
  1. Spike: does `"superpowers@synced": false` in `~/.claude/settings.json` turn superpowers off at user scope? Back up the file, test in a scratch project, restore. If it does not, stop and ask the user: D7 would fall back to superpowers on at user scope and off per trial project.
  2. Rehearsal: from a session started in one repo, run `kit:setup my` on a scratch copy of a different project, so the rehearsal also tests writing into another repo. If those writes are refused, the runbook's step 5 session needs `--add-dir`. Then approve the import once interactively and check with `claude -p` that the size table text is in context. This rehearses runbook steps 6 to 9.
  3. Declined once: in a scratch project, decline the import prompt, then start a new interactive session. Does it ask again? If not, the guard's advice and runbook step 8 must say how to reset `hasClaudeMdExternalIncludesWarningShown`.
  4. Parent folder: in a scratch folder holding a nested repo, put an import in the parent's `CLAUDE.md` and start a session in the nested repo. Record whether the parent's import loads and which path's approval flag it uses. The parent folders `diagoradisa/` and `grispy-web-ext/` hold no import under D13, so this only confirms that nothing reaches the nested repos twice.
  5. Import into the same repo: after the `~/.claude/methods` link exists in a scratch home, import `~/.claude/methods/my.md` from a project whose real path contains the target, as `claude-setup` does. Record whether Claude Code asks for approval and sets the flag. If it treats the import as internal and never sets the flag, the guard must also accept "the import's real path is inside the project root" as approved.
  6. Missing target: import a file that does not exist and start a session. Record whether Claude Code says anything. The Rollback section relies on silence.
- **After the cutover:** runbook steps 7 and 9.

## Trade-offs

- **Off by default (D7) vs on by default.** Off means a trial project cannot pick up superpowers by mistake, and an unset project gets a clean neutral core. The cost: all 21 `my` repos need a settings file before they work as today, and a project that was missed fails quietly, with no plugin and so no `my` hooks. The `kit` guard does not catch that miss, because a project with no import and our plugins off is the "neutral project" state. Runbook step 7 covers the 22 known repos; a project created later must run `kit:setup`.
- **One sitting (D11) vs an overlap period.** One sitting has no doubled text (about 60,000 characters) and no rule kept in two places. The cost: any session started before step 7 runs with a pending approval, which the guard reports, and the wait in step 1 can take a while.
- **`my` keeps its name (D3).** Fewer renames and no change to the commands the user types most. The cost: the name `my` now means "the method", while `kit` holds things that were also "mine". Committed docs keep `my:` names for neutral skills, which reads as a dead reference.
- **Guard reads an undocumented key.** The approval flag may change in a later Claude Code release. The guard treats a missing flag as "not approved", so a renamed key gives a false warning, not a silent miss.

## Dependencies

- No new packages. The guard uses the Python standard library, as the other hooks do.
- The undocumented `hasClaudeMdExternalIncludesApproved` key in `~/.claude.json`.
- The `superpowers@synced` key in `enabledPlugins`. Project scope is confirmed by spike 1; user scope is checked in task 0.
- A new symlink `~/.claude/methods`, and edits to `~/.claude/settings.json` and `~/bin`, all outside the repo.

## Risk

- **Hard to reverse:** the import line and settings file written into 22 repos. Moving `global/methods/` later means editing all of them and approving each import again. The rename of neutral skills to `kit:` is cheap by comparison.
- **Blast radius of the cutover:** every Claude session on this machine, in the 22 repos set up here and in every folder D19 lets go neutral. Runbook step 1 waits for other sessions; steps 7 and 9 check each repo.
- **Silent miss:** a project not set up gets the neutral core only, with no message. Detection: runbook step 7 for known repos. Projects started later rely on the user running `kit:setup`.
- **Worktree paths:** a session started inside a worktree folder has its own project path in `~/.claude.json` and so its own approval flag. `my:handoff` opens every stage at the repo root, so it is not affected. A session started by hand inside `.claude/worktrees/<name>` gets the guard's "not approved" warning and reads the method file.
- **Approval flag changes meaning:** the guard gives a false "not approved" warning, and the model reads the method file twice in effect. Detection: the warning appears in a project the user has approved.
- **Core boundary drawn wrong:** a rule moved to the method that should hold everywhere, or the reverse. `test_neutral_core.py` catches method text creeping back into the core; it does not catch a neutral rule wrongly moved out. The user reviews the section table in this spec.
- **Combined memory size:** `my` projects load the same text as today (about 30,000 characters, 42,000 when `docs/plans/` is touched). The size warning threshold is undocumented; nothing changes from today.
- **Conflicts with open `my:handoff` rows** in `ROADMAP.md` ("Trim copied facts in `my:handoff`", "Split `my:handoff` by mode"). Batch 1 does not move handoff files. Batch 2 edits one line of `plugins/my/skills/handoff/README.md`. A merge conflict there is small and shows at merge time.
- **Known limit:** the guard does not check that the method file's content loaded, only that the import exists and is approved. A typo inside `my.md` that breaks an `@` import of its own is not caught; `my.md` has no nested imports in this design.
- **Manual steps:** runbook steps 3, 4, 5, 6 and 8, and the batch 1 runbook. Steps 5 and 8 need the user at the keyboard.
- **Old worktrees:** a session started inside a worktree whose branch predates the setup commit runs with no method and no warning, until D20's merge. Detection: the runbook's `git worktree list` in step 6.
- **Plugin cache lag:** a session started before a `claude plugin update` runs the old plugin code. D17's steps cover the runbooks; any other session must restart after each batch.

## Open questions

None. Task 0 may reopen a decision: check 1 can reopen D7, and checks 3 and 5 can change the guard. If one does, the plan stops and asks.
