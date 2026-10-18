# Reetesh Kumar Gangwar — academic website

Website address: **https://reeteshgangwar.github.io**

Built with Quarto 1.10.19. This is the source for the GitHub repository
**ReeteshGangwar/ReeteshGangwar.github.io**.

## Routine updates: one document

Open **[UPDATE-WEBSITE.md](UPDATE-WEBSITE.md)**, click the pencil, and use the
example for the information you want to add. Change the opening code fence from
`example` to `update`, fill in the fields, and click **Commit changes**.

The publishing workflow checks the information, routes it to the correct page,
builds the site, checks local links, and deploys the result. A failing update does
not replace the previous successful website. Check the Actions tab if an update
has not appeared.

| Type | Destination |
|---|---|
| Publication | Publications, under its year/category |
| Student | Group, under programme and current/alumni status |
| Talk | Talks & Outreach, under its year and type |
| News | Homepage feed and full News archive |
| Project | Sponsored projects or consultancy |
| Teaching | Undergraduate or postgraduate course record |
| Award | About → Fellowships and honours |
| Profile | Homepage introduction or About biography |
| Page | An exact wording change on another page |

Use `Announce: Yes` and a Date to make a matching News item for a publication,
student, talk, project or award. Announcements use the same record; you do not
need to enter the information again. Five recent updates appear on Home, with
the complete feed in News.

**Keep active records in the update document.** Edit their fields to revise
information. Existing paper titles, doctoral student names and course codes
identify entries that should be replaced, avoiding duplicate entries.

This uses explicit fields rather than guessing the meaning of arbitrary text.
Photos must be uploaded inside `assets/` first; their path can then be used in a
Student entry. The provided PDF CV remains a separate file and is not regenerated
by this website update workflow.

## Initial GitHub Pages setup

1. Use the GitHub account `ReeteshGangwar`.
2. Create a public repository named **ReeteshGangwar.github.io**. If it already
   exists, inspect it before replacing or combining any files.
3. Upload or push this folder's source files, including `.github/workflows/`,
   `_content/`, `scripts/`, and assets. Do not upload the surrounding CV,
   Documents, or original Wix media folders. Do not upload `_site/` or `.quarto/`.
4. Set the default branch to `main`.
5. Under **Settings → Pages → Build and deployment → Source**, select
   **GitHub Actions**.
6. Run **Actions → Validate and publish website → Run workflow**, or commit a
   source change. The successful deployment reports the live URL.

The repository's default Actions token is used. No personal access token or API
key is required by this workflow.

## Local preview and validation

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
quarto render
quarto preview
```

The build uses only Python's standard library for update processing. Quarto
runs `scripts/build_updates.py` before rendering, and `scripts/check_site.py`
after rendering. The GitHub workflow installs the pinned Quarto release.

## Files for maintainers

- `UPDATE-WEBSITE.md`: the routine update document.
- `_content/base/*.qmd`: preserved original page content and layout. Edit here
  for a permanent redesign or base-content correction.
- Root `.qmd` files: generated from the base content plus active updates. Direct
  edits to these files are replaced at the next build.
- `styles.css`: shared typography, layout, and mobile rules.
- `_quarto.yml`: navigation, site address, and build hooks.
- `scripts/build_updates.py`: validation and routing; writes no pages on invalid
  input.
- `scripts/test_updates.py`: routing, replacement, archive, and failure tests.
- `scripts/check_site.py`: verifies expected pages, mobile metadata and local links.
- `.github/workflows/publish.yml`: build, validation, and Pages deployment.

No live GitHub deployment should be assumed until the Actions deployment has
completed successfully and the published URL has been checked.
