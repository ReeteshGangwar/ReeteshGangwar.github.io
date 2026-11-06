# Website Updates

This is the only document you need for routine content updates.

**To publish an update:** copy an example below to the **Active updates** section,
change its opening fence from `example` to `update`, fill in the details, then
click **Commit changes** in GitHub. Once GitHub Pages is connected, a successful
build places the information on the right page and publishes it automatically.

Keep active entries here: they are your saved records. Edit an existing block to
correct it; do not repeatedly add the same item. Examples do not appear online.
Your existing website content is preserved separately; updates are applied to it.

## Active updates

<!-- Paste your completed update blocks below this line. -->

```update
Type: Publication
ID: falling-film-plasma-uv-2026
Title: Synergistic falling film nonthermal plasma and UV-photon hybrid system: An advanced and energy-efficient approach for rapid dye degradation
Authors: T. Pushparaj Gandhi, Somya Pal, Sriramulu Maniteja, Reetesh Kumar Gangwar and Shihabudheen M. Maliyekkal
Journal: Separation and Purification Technology
Year: 2026
DOI: 10.1016/j.seppur.2026.140781
Category: Journal
Announce: Yes
Date: 2026-11-06
Details: Our new paper on a falling-film nonthermal plasma and UV-photon hybrid system for rapid dye degradation has been published in Separation and Purification Technology.
```
```update
Type: News
ID: psst-editorial-board-announcement-2026
Title: Editorial Board appointment at Plasma Sources Science and Technology
Date: 2026-11-06
Details: Appointed Editorial Board Member of Plasma Sources Science and Technology (IOP Publishing), effective October 2026.
URL: https://publishingsupport.iopscience.iop.org/journals/plasma-sources-science-and-technology/editorial-board/
```


```update
Type: Page
ID: psst-editorial-board-2026
Page: service
Find: **Guest Editor**, *IEEE Transactions on Plasma Science*, Special Issue on the 40th PSSI National Symposium on Plasma Science and Technology (PLASMA 2025) – [view special issue](https://ieeexplore.ieee.org/document/11349678)
Replace: **Editorial Board Member**, *Plasma Sources Science and Technology* (IOP Publishing), October 2026–present – [editorial board](https://publishingsupport.iopscience.iop.org/journals/plasma-sources-science-and-technology/editorial-board/). Also serving as **Guest Editor**, *IEEE Transactions on Plasma Science*, Special Issue on the 40th PSSI National Symposium on Plasma Science and Technology (PLASMA 2025) – [view special issue](https://ieeexplore.ieee.org/document/11349678)
```

## Examples — copy only the one you need

### News (homepage and full news archive)

```example
Type: News
Title: Your announcement title
Date: 2026-10-18
Details: Write your announcement here in normal sentences.
URL: https://example.com
```

The homepage shows the five newest entries added to this feed. The News page
keeps the full feed. Add newer announcements above older active blocks.

### Publication (Publications page, correct year)

```example
Type: Publication
Title: Full paper title
Authors: First Author, Second Author, and R. K. Gangwar
Journal: Full journal title
Year: 2026
DOI: 10.1234/example
Category: Journal
Announce: Yes
Date: 2026-10-18
Details: A brief description for the news announcement.
```

Category: `Journal`, `Preprint`, `Chapter`, or `Patent`.
Use `URL: https://...` instead of DOI when appropriate. DOI and URL are optional.
Use `Announce: No` to update only Publications; Date is then optional.
For patents, Journal can identify the patent office or disclosure record.

### Student or researcher (Group page)

```example
Type: Student
Name: Full name
Programme: PhD
Status: Current
Topic: Research topic in one sentence
Year: 2026
Photo: assets/media/filename.webp
```

Programme: `PhD`, `Postdoc`, `MS`, `MSc`, `MTech`, or `Project`.
Status: `Current` or `Alumni`. For a PhD graduate, change Status to Alumni,
add `EndYear: 2026` and optionally `Position: Current appointment`.
An existing doctoral student's entry is replaced rather than duplicated.
Photo is optional; upload the photo first and give its local assets/ path.
When revising an existing student, include their photo path to keep the image.
For legacy master's names in a shared list, use the Page example instead.

### Talk (Talks & Outreach, correct year)

```example
Type: Talk
Title: Full presentation title
Date: 2026-10-18
EndDate: 2026-10-20
Event: Conference or host institution and location
Kind: Invited talk
```

EndDate is optional. Kind may be `Invited talk`, `Keynote`, `FDP lecture`,
`Training`, `Popular talk`, or `Tutorial`. Dates can also be written as
`18 October 2026`. Use the event dates if the exact presentation date is unknown.

### Project (Projects page)

```example
Type: Project
Title: Project title
Agency: Funding agency or company
Role: PI
Year: 2026
EndYear: 2029
Status: Ongoing
Kind: Sponsored
Funding: INR 25 lakh
Details: Optional short description
```

Role: PI or Co-PI. Kind: Sponsored or Consultancy.
Funding, EndYear and Details are optional.

### Course (Teaching page)

```example
Type: Teaching
Code: PH605L
Title: Basics and Applications of Plasma Physics
Level: Postgraduate
Semesters: Jul–Dec 2026, Jul–Dec 2025
```

Level: Undergraduate or Postgraduate. Using the same course code replaces its
entry, so retain all semesters you want shown.

### Award (About page)

```example
Type: Award
Title: Name of award or honour
Year: 2026
Details: Awarding organization and relevant context
```

### Biography or homepage introduction

```example
Type: Profile
Field: research-introduction
Text: Write the complete replacement research introduction here.
```

Field: `research-introduction` for Home, or `biography` for About.
This replaces that paragraph; it does not append another one.

### Any other wording on a page

```example
Type: Page
Page: research
Find: Exact existing sentence copied from that page's source.
Replace: The replacement sentence you want.
```

Page names: index, about, research, publications, projects, group, teaching,
service, talks, news, contact, cv. Find must match exactly once.
For a substantial redesign, ask for a layout change rather than using this form.

## Important details

- An `update` block is active. An `example` block is not active.
- Type and field names are case-insensitive. Use one `Field: value` per line.
- A long Details or Text value can continue on the next line if indented.
- Student names, paper titles and course codes identify existing entries. Keep
  them consistent when revising an item. Use the Page example to correct a title.
- Optional `ID: my-stable-id` lets a later complete block supersede another
  active block with the same ID and Type.
- `Announce: Yes` plus a Date creates a matching homepage/news announcement for
  Publication, Student, Talk, Project or Award updates. The news links to its page.
- Required fields, dates, photo paths and link formats are checked. Invalid
  updates stop the build; the previous successful live site stays available.
- Saving a file only on your Mac does not upload it. Commit the update on GitHub,
  or push your local changes. The live workflow begins only after GitHub setup.
- The downloadable PDF CV remains a separate supplied file. This workflow
  updates the website; it does not yet regenerate or modify the PDF CV.
