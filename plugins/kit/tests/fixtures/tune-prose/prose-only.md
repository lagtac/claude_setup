---
name: release-notes
description: >
  Write release notes for a version tag. Use when the user asks for release
  notes or types /release-notes <tag>. NOT for CHANGELOG edits. This skill
  checks the target file, finds the previous tag, reads the git log between
  the two tags, groups the commits by type, writes a notes file with a
  Summary, a Changes and an Upgrade steps section, and asks the user before
  it saves the file.
---

# Release notes

Git keeps the history of every commit, so the log holds all the changes
since the previous tag.

## Steps

1. If no tag was given, stop and ask for one. If
   `docs/release-notes/<tag>.md` already exists, stop and say so. Do not
   overwrite an existing file.
2. Find the previous tag with `git describe --tags --abbrev=0 <tag>^`. If
   there is none, stop and say so.
3. Run `git log --no-merges --format='%h %s%n%b%n---' <previous>..<tag>`.
   Each commit ends at a `---` line.
4. Group the commits by their Conventional Commit type into `feat`, `fix`
   and `other`. Every other type, and every commit with no type, goes in
   `other`. A commit is breaking when its subject has `!` before the colon
   or its body has a `BREAKING CHANGE:` footer.
5. Write the notes with this template:

   ```markdown
   ## Summary
   <one paragraph: what the version changes for a user>

   ## Changes
   - <one bullet per non-breaking commit, in the order feat, fix, other>

   ## Upgrade steps
   - <one bullet per breaking commit, or "None">
   ```

   That is three sections: Summary, Changes and Upgrade steps. Use them as
   given.
6. Ask the user before saving. If `AskUserQuestion` is not available, print
   the notes, say that replying "save" writes them to
   `docs/release-notes/<tag>.md`, and end the turn.

## Rules

- The project's `CLAUDE.md` wins over this template when the two differ.
- Breaking commits go under Upgrade steps, not under Changes. (Added on
  2026-04-11 after row 31 found that a release hid a breaking change; 12 of
  40 releases had missed one.)
- Take each upgrade step from the commit's `BREAKING CHANGE:` footer, as an
  action, because a reader follows Upgrade steps one by one while upgrading.
  When the footer states no action, write the subject and "action not
  stated in commit `<hash>`".
- Each breaking commit belongs under Upgrade steps, and only there.
