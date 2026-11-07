---
title: CV automation baseline
tags: [profile, cv, website, automation]
updated: 2026-11-07
---

# CV automation baseline

These explicitly selected LaTeX files and photo preserve the academic CV layout
from [[AI_reetesh_work/03_Academic-Profile/CV/README|the original CV project]].
The originals have not been changed. This baseline belongs to the website
repository so GitHub can build without access to the surrounding private vault.

## Status

The generator is integrated into the website pre-render step. GitHub Actions
uses TeX Live 2025 and pdfLaTeX to compile the PDF before rendering the website. Preview
builds on non-main branches do not deploy to GitHub Pages. A `CV-preview` artifact
is retained after each successful build for review.

## Intended routine

Enter structured records in `UPDATE-WEBSITE.md`. Publication,
Student, Talk, Project, Teaching, Award and Service records are applied to the CV
as well as their website pages. `Announce: Yes` and `Date` additionally create
News announcements for supported types. News, Profile and arbitrary Page edits
are website-only; appointments should use Service.

Keep active records. Each build starts from this baseline, applies records once,
and writes generated TeX under `archive/cv-build/`. Do not edit generated files.
Matching titles, names or course codes replace existing CV records; ambiguous
matches fail. Keep those identities stable when revising entries. Entries inside
the historical shared master's-student table require conversion to individual
records first; the generator stops rather than replace that entire table.

The historical publication selection (2024–2026) is preserved, with new records
added. Old manually calculated aggregate project totals are suppressed when a
Project update is present, to avoid publishing incorrect totals.

Biography, contact details, education, employment, memberships and general CV
layout still live in the baseline LaTeX. A future structured record type is
needed to automate changes to these sections. Overleaf edits are not synchronized
automatically with this baseline.

## Checks

From the website directory, using the research environment locally:

```sh
conda run -n research python -m unittest discover -s scripts -p 'test_*.py' -v
conda run -n research python scripts/build_cv.py --sources-only
```

Full local builds require `latexmk`, pdfLaTeX and the packages used by the
preserved template. GitHub Actions supplies a complete TeX Live 2025 environment,
compiles the prepared sources, and verifies the PDF matches the current sources
before Quarto renders the website. The pre-render step reuses that verified PDF
only when the source fingerprint matches. A CV failure stops publication before
the served PDF is replaced.

The current integration proposal is in
[[AI_reetesh_work/03_Academic-Profile/Website/output/CV-Automation-Review|CV automation review]].
