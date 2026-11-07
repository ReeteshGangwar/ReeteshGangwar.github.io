#!/usr/bin/env python3
"""Apply shared website records to preserved LaTeX sections, then compile the CV.

No baseline files are modified. Generated sources are disposable. The served
PDF is replaced only after a successful compiler exit and PDF signature check.
"""
from pathlib import Path
import argparse
import re
import shutil
import subprocess
import sys

from build_updates import ROOT, parse_updates, norm, compile_pages

SECTIONS = ('research-interests', 'education', 'experience', 'awards',
            'projects', 'publications', 'teaching', 'scholars', 'activities',
            'service', 'memberships')
ENTRY = re.compile(r'\\entry\*\[.*?(?=\\entry\*\[|\\subrubric\{|\\end\{rubric\})', re.S)


def tex(value):
    """Escape user text in one pass; never treat update text as TeX commands."""
    replacements = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%',
                    '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{',
                    '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
                    '–': '--', '—': '---', '’': "'", '“': '``', '”': "''"}
    return ''.join(replacements.get(c, c) for c in value)


def text_key(value):
    value = re.sub(r'\\(?:href|doi|artlink)\{[^}]*\}', '', value)
    value = re.sub(r'\\[A-Za-z]+\*?', '', value)
    return norm(value)


def remove_entry(source, needle, scope=None):
    """Match entire normalized identities; refuse ambiguous replacements."""
    key = text_key(needle)
    start, end = 0, len(source)
    if scope:
        marker = r'\subrubric{' + scope + '}'
        start = source.find(marker)
        if start < 0:
            return source, False
        end_match = re.search(r'\\subrubric\{|\\end\{rubric\}', source[start + len(marker):])
        end = start + len(marker) + end_match.start() if end_match else len(source)
    matches = [m for m in ENTRY.finditer(source) if start <= m.start() < end
               and (' ' + key + ' ') in (' ' + text_key(m[0]) + ' ')]
    if len(matches) > 1:
        raise ValueError('Ambiguous CV record: ' + needle)
    if not matches:
        return source, False
    m = matches[0]
    if r'\begin{tabular}' in m[0]:
        raise ValueError('This CV entry contains a shared student table. Convert that table to individual records before updating: ' + needle)
    return source[:m.start()] + source[m.end():], True


def insert_entry(source, heading, body):
    entry = body.rstrip() + '\n'
    if not heading:
        marker = re.search(r'\\begin\{rubric\}\{[^}]+\}', source)
        return source[:marker.end()] + '\n' + entry + source[marker.end():]
    marker = r'\subrubric{' + heading + '}'
    at = source.find(marker)
    if at >= 0:
        at += len(marker)
        return source[:at] + '\n' + entry + source[at:]
    # Keep dated publication subsections newest first within their category.
    heading_year = re.fullmatch(r'(.+ -- )([0-9]{4})', heading)
    if heading_year:
        for old in re.finditer(r'\\subrubric\{([^}]+)\}', source):
            old_year = re.fullmatch(r'(.+ -- )([0-9]{4})', old[1])
            if old_year and old_year[1] == heading_year[1] and old_year[2] < heading_year[2]:
                return source[:old.start()] + marker + '\n' + entry + source[old.start():]
    at = source.index(r'\end{rubric}')
    return source[:at] + marker + '\n' + entry + source[at:]


def compile_sections(base, records):
    sections = dict(base)
    if any(r['type'] == 'publication' for r in records):
        sections['publications'] = re.sub(r'\\begin\{rubric\}\{Publications[^}]*\}',
                                         lambda _: r'\begin{rubric}{Publications}',
                                         sections['publications'], count=1)
    for r in records:
        kind = r['type']
        if kind in ('news', 'profile', 'page'):
            # News is not a CV entry. Arbitrary page edits and biography text
            # cannot safely be translated to structured CV section updates.
            continue
        p = lambda name: tex(r.get(name, ''))
        title = r.get('title', r.get('name', r.get('code', '')))
        label = r.get('year', r.get('date', ''))
        heading = None
        scope = None
        if kind == 'publication':
            section = 'publications'
            category = r.get('category', 'journal').lower()
            heading = {'journal': 'Journal Articles -- ' + r.get('year', ''),
                       'preprint': 'Preprints (arXiv)', 'chapter': 'Book Chapter -- ' + r.get('year', ''),
                       'patent': 'Patents'}[category]
            body = p('authors') + ", ``" + p('title') + "'', " + r'\emph{' + p('journal') + '} (' + p('year') + ').'
            if r.get('doi'):
                body += r' \doi{' + p('doi') + '}'
            elif r.get('url'):
                body += r' \artlink{' + p('url') + '}'
            label = ''
        elif kind == 'teaching':
            section = 'teaching'
            heading = 'Undergraduate Courses' if r.get('level', '').lower() == 'undergraduate' else 'Postgraduate and Ph.D. Courses'
            title = r['code']
            label = title
            body = r'\textbf{' + p('title') + r'}\par ' + p('semesters')
        elif kind == 'award':
            section = 'awards'
            body = r'\textbf{' + p('title') + '} -- ' + p('details')
        elif kind == 'project':
            section = 'projects'
            heading = 'Consultancy Projects' if r.get('kind', '').lower() == 'consultancy' else 'Sponsored Research Projects'
            scope = heading  # Same title can occur under two different grants.
            label += (' -- ' + r['endyear']) if r.get('endyear') else ''
            body = r'\textbf{' + p('agency') + '} -- ' + p('role') + ' -- ' + p('status')
            if r.get('funding'):
                body += ' -- ' + p('funding')
            body += r'\par\emph{' + p('title') + '}'
            if r.get('details'):
                body += r'\par ' + p('details')
        elif kind == 'talk':
            section = 'activities'
            heading = 'Faculty Development Programmes and Popular Talks' if any(w in r.get('kind', '').lower() for w in ('fdp', 'training', 'popular', 'tutorial', 'lecture')) else 'Keynote and Invited Talks'
            label = r.get('date', '') + (' -- ' + r['enddate'] if r.get('enddate') else '')
            body = p('kind') + ': ' + r'\emph{' + p('title') + '}, ' + p('event')
        elif kind == 'student':
            section = 'scholars'
            programme = r.get('programme', '')
            alumni = r.get('status', '').lower() == 'alumni'
            heading = ('Ph.D. Graduates' if alumni else 'Ph.D. Scholars (ongoing)') if programme.lower() == 'phd' else programme + (' Alumni' if alumni else ' Researchers and Students')
            label += (' -- ' + r.get('endyear', 'completed')) if alumni else (' -- present' if label else '')
            body = r'\textbf{' + p('name') + '} -- ' + p('topic')
            if r.get('position'):
                body += r'\par Now: ' + p('position')
        elif kind == 'service':
            section = 'service'
            heading = r.get('section', 'Service to the Scientific Community')
            label = r.get('period', r.get('date', ''))
            body = r'\textbf{' + p('title') + '} -- ' + p('details')
            if r.get('url'):
                body += r' \artlink{' + p('url') + '}'
        else:
            raise ValueError('Unsupported CV type: ' + kind)
        updated, found = remove_entry(sections[section], title, scope)
        if r.get('action') == 'remove':
            if not found:
                raise ValueError('CV removal did not match an existing entry: ' + title)
        else:
            updated = insert_entry(updated, heading, r'\entry*[' + tex(label) + r'] \small ' + body)
        sections[section] = updated
    # A changing project set invalidates the manually typed aggregate totals.
    if any(r['type'] == 'project' for r in records):
        sections['projects'] = re.sub(r'\\entry\*\[\].*?(?=\\subrubric)', '', sections['projects'], count=1, flags=re.S)
    return sections


def build(root=ROOT, source=None, work=None, compile_pdf=True, destination=None):
    root = Path(root)
    source = Path(source) if source else root / '_content/cv'
    work = Path(work) if work else root / 'archive/cv-build'
    records = parse_updates((root / 'UPDATE-WEBSITE.md').read_text())
    # Standalone CV builds enforce the same categories, sections and asset paths
    # as website builds before any output file is written.
    compile_pages({p.stem: p.read_text() for p in (root / '_content/base').glob('*.qmd')}, records, root)
    base = {name: (source / (name + '.tex')).read_text() for name in SECTIONS}
    sections = compile_sections(base, records)
    work.mkdir(parents=True, exist_ok=True)
    for name in ('cv-llt.tex', 'settings.sty', 'photo.jpg'):
        shutil.copyfile(source / name, work / name)
    for name, text in sections.items():
        (work / (name + '.tex')).write_text(text)
    if not compile_pdf:
        return work
    executable = shutil.which('tectonic')
    if not executable:
        raise ValueError('Tectonic is required to build the CV PDF.')
    subprocess.run([executable, '--untrusted', '--keep-logs', 'cv-llt.tex'], cwd=work, check=True)
    pdf = work / 'cv-llt.pdf'
    if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
        raise ValueError('Compiler did not produce a valid CV PDF.')
    destination = Path(destination) if destination else root / 'assets/Reetesh-Gangwar-CV.pdf'
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.pdf.tmp')
    shutil.copyfile(pdf, temporary)
    temporary.replace(destination)
    print('CV built successfully: ' + str(destination))
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--sources-only', action='store_true')
    args = parser.parse_args()
    try:
        build(source=args.source, work=args.work, destination=args.destination, compile_pdf=not args.sources_only)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print('CV BUILD ERROR: ' + str(error), file=sys.stderr)
        sys.exit(1)
