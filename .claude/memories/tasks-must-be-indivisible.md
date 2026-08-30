---
name: tasks-must-be-indivisible
description: Every task in Claude Code's native structured task list must be indivisible.
metadata:
  type: feedback
---

Each task created with `TaskCreate` must be indivisible: one atomic unit of
work that cannot be meaningfully broken down further. Never file a task that
bundles several independent pieces of work.

**Why:** A divisible task hides its own progress. "Split multi-assert tests"
reads as one line whether nine files remain or one, so the list stops
reflecting the real state of the work and stops being useful to the user.

**How to apply:** Before creating a task, ask whether it could be split. If it
could, file the parts instead. Prefer one task per file, per check, or per
fix. Split a task in flight the moment it turns out to have been divisible.
See [[md-paragraphs-wrap-at-80]] and [[push-directly-to-main]].
