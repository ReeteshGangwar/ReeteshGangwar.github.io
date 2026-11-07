---
title: Brief website CV v2
tags: [profile, website, cv, automation]
updated: 2026-11-07
---

# Brief website CV v2

The source and photograph here preserve the newer v2 CV supplied by the owner.
The website publishes this brief version. The detailed v1 CV is a separate
local personal document, outside the website repository.

`scripts/build_cv_v2.py` applies structured records from `UPDATE-WEBSITE.md`
to v2's native entries. It retains the preamble, header, tables, memberships,
unchanged content, bold author name and known supervised-author underlining.
Both original CV sources in the separate CV project remain unchanged.

Publication, Student, Talk, Project, Teaching, Award and Service records update
the CV. News, Profile and arbitrary Page wording edits affect the website only.
Use Service for appointments shared with the CV. Keep active blocks and stable
identifying titles, names and course codes when revising records.

Student updates refresh PhD graduation/current counts. Project funding summaries
are recomputed when all amounts are available; otherwise the summary refers to
the project records. Citation metrics retain their explicitly dated snapshot.
Existing names in the shared master's table need conversion to individual
records first; the build refuses to replace that whole table as one person.

GitHub Actions generates sources in `archive/cv-build/`, compiles them with
TeX Live 2025/pdfLaTeX, verifies the source fingerprint, and renders the website.
Preview branches keep a `CV-preview` artifact but cannot deploy to Pages.
The served PDF is replaced only after successful compilation and validation.

Full local builds require latexmk/pdfLaTeX and the template packages. The
personal CV project supplies a local command for rebuilding both formats from
the same update records. Its detailed sources and outputs are not uploaded.
