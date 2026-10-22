---
name: release-notes
description: >
  Write release notes for a version tag. Use when the user asks for release
  notes or types /release-notes <tag>. NOT for CHANGELOG edits. This skill
  reads the git log since the previous tag, groups the commits by type,
  writes a notes file with a Summary, a Changes and an Upgrade steps section,
  and asks the user before it saves the file. It works in any git repository.
---

# Release notes

This skill works for any project that uses git. Git keeps the history of
every commit, so the log holds all the changes since the previous tag.

Spec: `docs/plans/2026-03-02-release-notes-spec.md`.

## Steps

1. Find the previous tag with `git describe --tags --abbrev=0 <tag>^`. If
   there is none, stop and say so.
2. Run `git log --format='%s%n%b' <previous>..<tag>`.
3. Group the commits by their Conventional Commit type: `feat`, `fix`, and
   `other`. Commits with no type usually go in `other`. A commit is breaking
   when its subject has `!` before the colon or its body has a
   `BREAKING CHANGE:` footer.
4. Write the notes with this template:

   ```markdown
   ## Summary
   <one paragraph: what the version changes for a user>

   ## Changes
   - <one bullet per non-breaking commit, grouped feat, fix, other>

   ## Upgrade steps
   - <one bullet per breaking commit, or "None">
   ```

   That is three sections: Summary, Changes and Upgrade steps. Use them as
   given.
5. Ask the user before saving the file. If `AskUserQuestion` is not
   available, print the notes and stop.
6. Save to `docs/release-notes/<tag>.md`. If the file already exists, stop
   and say so. Do not overwrite an existing file.

## Rules

- The project's `CLAUDE.md` wins over this template when the two differ.
- Breaking commits go under Upgrade steps, not under Changes. (Added on
  2026-04-11 after row 31 found that a release hid a breaking change; 12 of
  40 releases had missed one.)
- Write each upgrade step as an action, because a reader follows Upgrade
  steps one by one while upgrading.
- Each breaking commit belongs under Upgrade steps, and only there.
