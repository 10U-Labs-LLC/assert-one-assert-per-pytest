---
name: push-directly-to-main
description: This repo pushes directly to main; do not create a branch or PR for routine changes.
metadata:
  type: feedback
---

We push directly to `main` in this repo. Do not create a feature branch or open a PR unless explicitly asked.

**Why:** Small solo-maintained repo; the branch/PR ceremony in the early history is not the working convention.

**How to apply:** When asked to commit or push, commit on `main` and `git push` — even though `main` is the default branch.
