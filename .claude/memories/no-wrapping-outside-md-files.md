---
name: no-wrapping-outside-md-files
description: GitHub issue and PR bodies get no hard wrapping at all; the 80-character rule is for .md files only.
metadata:
  type: feedback
---

Do not hard-wrap text written outside `.md` files. GitHub issue bodies, PR
descriptions, and comments get one line per paragraph and per list item, with no
newline characters inside either.

**Why:** The 80-character rule exists to keep diffs of checked-in files
readable. An issue body has no diff to keep clean, GitHub wraps it to the
reader's own column, and hard newlines make the web editor and quote-replies
awkward.

**How to apply:** Apply [[md-paragraphs-wrap-at-80]] only to `.md` files in the
repository. Everywhere else, write each paragraph as a single line. Do not
describe this as "soft-wrapping" — there is no wrapping of any kind.
