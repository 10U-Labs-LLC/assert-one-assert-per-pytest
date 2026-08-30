---
name: md-paragraphs-wrap-at-80
description: In .md files only prose paragraphs wrap at 80 characters; other constructs may run long.
metadata:
  type: feedback
---

In Markdown files, the 80-character limit applies only to prose paragraphs.
List items, headings, tables, link lines, and code blocks may exceed it.

**Why:** Hard-wrapping non-paragraph constructs hurts readability and makes
diffs noisier than the width saves. markdownlint's MD013 cannot express the
distinction, so it is disabled in `.github/workflows/documentation.yml` rather
than satisfied by rewrapping.

**How to apply:** Wrap paragraph prose at 80. Leave a long list item, heading,
or table row on one line instead of folding it. Do not re-enable MD013 or add
line-length rewrapping to satisfy a linter. See [[push-directly-to-main]].
