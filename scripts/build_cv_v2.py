"""Apply shared records to the original v2 article layout without flattening it.

Keep the preamble, header, photograph, tables and all unmodified entries from v2.
Read balanced TeX groups because entries contain nested formatting commands.
"""
import re
from datetime import date
from decimal import Decimal
from build_updates import parse_date


def group(text, start):
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != '{':
        raise ValueError('Expected a braced TeX argument.')
    depth = 0
    for pos in range(start, len(text)):
        slash = pos - 1
        while slash >= 0 and text[slash] == '\\':
            slash -= 1
        if (pos - slash - 1) % 2:
            continue
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:pos], pos + 1
    raise ValueError('Unbalanced TeX group.')


def entries(text, command='dated'):
    result = []
    for match in re.finditer(r'\\' + command + r'\s*\{', text):
        label, end = group(text, match.end() - 1)
        body, end = group(text, end)
        result.append((match.start(), end, label, body))
    return result


def heading_key(value):
    from build_cv import text_key
    return text_key(re.sub(r'\s*\(\d+\)\s*$', '', value))


def bounds(text, heading):
    headings = list(re.finditer(r'\\subsection\*\{([^}]+)\}', text))
    for i, match in enumerate(headings):
        if heading_key(match[1]) == heading_key(heading):
            return match.end(), headings[i + 1].start() if i + 1 < len(headings) else len(text)
    return None


def remove(text, title, command='dated', scope=None, fallback=None):
    from build_cv import text_key
    key = ' ' + text_key(title) + ' '
    span = bounds(text, scope) if scope else (0, len(text))
    candidates = [e for e in entries(text, command) if span and span[0] <= e[0] < span[1]]
    matches = [e for e in candidates if key in ' ' + text_key(e[2] + ' ' + e[3]) + ' ']
    if not matches and fallback:
        matches = [e for e in candidates if fallback(e)]
    if len(matches) > 1:
        raise ValueError('Ambiguous v2 CV identity: ' + title)
    if not matches:
        for table in re.finditer(r'\\begin\{tabularx\}.*?\\end\{tabularx\}', text, re.S):
            if key in ' ' + text_key(table[0]) + ' ':
                raise ValueError('This name is in a shared student table; convert it to individual records first: ' + title)
        return text, False
    start, end, _, _ = matches[0]
    return text[:start] + text[end:], True


def insert(text, body, heading=None):
    if heading:
        span = bounds(text, heading)
        if span:
            at = span[0]
        else:
            # Add missing journal years in reverse chronological order.
            new_year = re.fullmatch(r'(Journal articles -- )([0-9]{4})', heading)
            if new_year:
                old = [m for m in re.finditer(r'\\subsection\*\{Journal articles -- ([0-9]{4})\}', text) if m[1] < new_year[2]]
                if old:
                    at = old[0].start()
                    return text[:at] + '\\subsection*{' + heading + '}\n' + body + '\n' + text[at:]
            return text.rstrip() + '\n\\subsection*{' + heading + '}\n' + body + '\n'
    else:
        marker = re.search(r'\\sectionnb\{[^}]+\}', text)
        if not marker:
            raise ValueError('Missing v2 section heading.')
        at = marker.end()
    return text[:at] + '\n' + body + '\n' + text[at:]


def authors(value, baseline):
    from build_cv import tex, text_key
    supervised = {text_key(m[1]) for m in re.finditer(r'\\stu\{([^}]+)\}', baseline)}
    parts = re.split(r'(,\s*|\s+and\s+)', value)
    result = []
    for part in parts:
        key = text_key(part)
        if key in {'r k gangwar', 'reetesh k gangwar', 'reetesh kumar gangwar'}:
            result.append(r'\me{}')
        elif key in supervised:
            result.append(r'\stu{' + tex(part) + '}')
        else:
            result.append(tex(part))
    return ''.join(result)


def compile_v2(document, records):
    from build_cv import tex, text_key
    markers = list(re.finditer(r'^%% ={3,} ([A-Z ]+) ={3,}\s*$', document, re.M))
    blocks = {m[1]: document[m.start():markers[i + 1].start() if i + 1 < len(markers) else len(document)] for i, m in enumerate(markers)}
    preamble = document[:markers[0].start()]
    # Stamp the generated copy only; never edit either original CV source.
    preamble = re.sub(r'Curriculum Vitae \\textperiodcentered\\ [A-Z][a-z]+ \d{4}',
                      lambda _: 'Curriculum Vitae ' + r'\textperiodcentered\ ' + date.today().strftime('%B %Y'), preamble)
    for r in records:
        kind = r['type']
        if kind in ('news', 'profile', 'page'):
            continue
        p = lambda name: tex(r.get(name, ''))
        title = r.get('title', r.get('name', r.get('code', '')))
        label = r.get('year', '')
        heading = scope = fallback = None
        command = 'dated'
        if kind == 'publication':
            block = 'PUBLICATIONS'; command = 'pub'
            category = r.get('category', 'journal').lower()
            heading = {'journal':'Journal articles -- ' + r.get('year', ''), 'preprint':'Under review', 'chapter':'Book chapter -- ' + r.get('year', ''), 'patent':'Patents'}[category]
            body = authors(r.get('authors', ''), document) + ", ``" + p('title') + "'', " + r'\emph{' + p('journal') + '} (' + p('year') + ').'
            if r.get('doi'):body += r' \doi{' + p('doi') + '}'
            elif r.get('url'):body += r' \lnk{' + p('url') + '}'
            label = r.get('id', 'update')
        elif kind == 'service':
            block = 'SERVICE'
            heading = {'Administrative Responsibilities at IIT Tirupati':'Major administrative responsibilities at IIT Tirupati', 'Service to the Scientific Community':'Service to the scientific community', 'Conference organization':'Conference organization'}[r.get('section', 'Service to the Scientific Community')]
            label = r.get('period', '')
            body = r'\textbf{' + p('title') + '} -- ' + p('details')
            if r.get('url'):body += r' \lnk{' + p('url') + '}'
        elif kind == 'award':
            block = 'HONOURS'; body = r'\textbf{' + p('title') + '} -- ' + p('details')
        elif kind == 'talk':
            block = 'TALKS'
            label = parse_date(r['date']).strftime('%b %Y') if r.get('date') else ''
            body = p('kind') + ': ' + r'\emph{' + p('title') + '}, ' + p('event')
            if r.get('date'):body += r'\sub{' + p('date') + (' -- ' + p('enddate') if r.get('enddate') else '') + '}'
        elif kind == 'student':
            block = 'SUPERVISION'; programme = r.get('programme', '').lower(); alumni = r.get('status', '').lower() == 'alumni'
            heading = ('Ph.D. graduates' if alumni else 'Ph.D. scholars, ongoing') if programme == 'phd' else {'postdoc':'Postdoctoral fellow', 'ms':r'M.S. (Research)'}.get(programme, r.get('programme', '') + ' students')
            label += (' -- ' + r.get('endyear', 'completed')) if alumni else (' -- present' if label else '')
            body = r'\textbf{' + p('name') + '} -- ' + r'\emph{' + p('topic') + '}'
            if r.get('position'):body += r'\sub{Now: ' + p('position') + '}'
        elif kind == 'project':
            block = 'PROJECTS'; heading = 'Industry consultancy' if r.get('kind', '').lower() == 'consultancy' else 'Sponsored research projects'; scope = heading
            label += (' -- ' + r['endyear']) if r.get('endyear') else ''
            body = r'\textbf{' + p('agency') + r'} \hfill{\small\sffamily ' + p('role') + '}'
            if r.get('funding'):
                amount = re.fullmatch(r'(?:INR|Rs\.?)?\s*([\d.]+)\s*(lakh|crore)', r['funding'], re.I)
                body += r' \amt{' + str(Decimal(amount[1]) * (100 if amount[2].lower() == 'crore' else 1)) + '}' if amount else ' -- ' + p('funding')
            body += ' -- ' + p('status') + r'\sub{\emph{' + p('title') + '}}'
            if r.get('details'):body += r'\sub{' + p('details') + '}'
            if r.get('agency') and r.get('year'):
                fallback = lambda e: text_key(r['agency']) in text_key(e[3]) and r['year'] in e[2]
        elif kind == 'teaching':
            block = 'TEACHING'; section = blocks[block]
            rows = list(re.finditer(r'^([^\n&]+) & ([^\n]+?) & ([^\n]+?) \\\\(?:\[[^]]+\])?\s*$', section, re.M))
            matches = [m for m in rows if (' ' + text_key(r['code']) + ' ') in (' ' + text_key(m[1]) + ' ')]
            if len(matches) > 1:raise ValueError('Ambiguous course code in v2: ' + r['code'])
            if matches:section = section[:matches[0].start()] + section[matches[0].end():]
            if r.get('action') != 'remove':
                level = 'Undergraduate' if r['level'].lower() == 'undergraduate' else 'Postgraduate'
                marker = re.search(r'^\\multicolumn[^\n]*' + level + r'[^\n]*$', section, re.M)
                if not marker:raise ValueError('Missing v2 course table level.')
                new_row = p('code') + ' & ' + p('title') + ' & ' + p('semesters') + r' \\'
                section = section[:marker.end()] + '\n' + new_row + section[marker.end():]
            blocks[block] = section; continue
        else:
            raise ValueError('Unsupported v2 update type: ' + kind)
        section, found = remove(blocks[block], title, command, scope, fallback)
        if r.get('action') == 'remove':
            if not found:raise ValueError('CV removal did not match v2: ' + title)
        else:
            # Long prose labels otherwise collide with the content column.
            label = label.replace('October', 'Oct').replace('November', 'Nov').replace('September', 'Sep')
            entry = '\\' + command + '{' + tex(label) + '}{' + body + '}'
            section = insert(section, entry, heading)
        blocks[block] = section
    if any(r['type'] == 'student' for r in records):
        counts = []
        for heading in ('Ph.D. graduates', 'Ph.D. scholars, ongoing'):
            span = bounds(blocks['SUPERVISION'], heading)
            count = len(entries(blocks['SUPERVISION'][span[0]:span[1]])) if span else 0
            counts.append(count)
            blocks['SUPERVISION'] = re.sub(r'(\\subsection\*\{Ph\.D\.\\?\s*' + ('graduates' if heading.endswith('graduates') else 'scholars, ongoing') + r')(?: \(\d+\))?(\})', lambda m:m[1] + ' (' + str(count) + ')' + m[2], blocks['SUPERVISION'])
        profile = blocks['PROFILE AT A GLANCE']
        for start, end, number, caption in reversed(entries(profile, 'stat')):
            if 'ph d students' in text_key(caption):profile = profile[:start] + '\\stat{' + str(counts[0]) + r'\,+\,' + str(counts[1]) + '}{' + caption + '}' + profile[end:]
        blocks['PROFILE AT A GLANCE'] = profile
    if any(r['type'] == 'project' for r in records):
        projects = entries(blocks['PROJECTS'])
        amounts = [re.search(r'\\amt\{([\d.]+)\}', e[3]) for e in projects]
        profile = blocks['PROFILE AT A GLANCE']
        for start, end, number, caption in reversed(entries(profile, 'stat')):
            if 'research funding' in text_key(caption):
                if all(amounts):
                    total = sum(Decimal(a[1]) for a in amounts)
                    pi = sum(bool(re.search(r'(?<!Co-)\bPI\b', e[3].split(r'\sub', 1)[0])) for e in projects)
                    tile = '\\stat{\\rs' + format(total / 100, '.2f') + ' Cr}{research funding\\\\' + str(len(projects)) + ' projects, PI on ' + str(pi) + '}'
                else:tile = r'\stat{\textemdash}{research funding\\see project records}'
                profile = profile[:start] + tile + profile[end:]
        blocks['PROFILE AT A GLANCE'] = profile
    years = [int(r['year']) for r in records if r['type'] == 'publication' and r.get('year')]
    if any(r['type'] == 'publication' for r in records):
        span = bounds(blocks['PUBLICATIONS'], 'Patents')
        count = len(entries(blocks['PUBLICATIONS'][span[0]:span[1]], 'pub')) if span else 0
        profile = blocks['PROFILE AT A GLANCE']
        for start, end, number, caption in reversed(entries(profile, 'stat')):
            if 'patent' in text_key(caption):
                profile = profile[:start] + '\\stat{' + str(count) + '}{' + caption + '}' + profile[end:]
        blocks['PROFILE AT A GLANCE'] = profile
    if years:
        blocks['PUBLICATIONS'] = re.sub(r'(\\sectionnb\{Publications), (\d{4}) -- (\d{4})(\})', lambda m:m[1] + ', ' + str(min(int(m[2]), *years)) + ' -- ' + str(max(int(m[3]), *years)) + m[4], blocks['PUBLICATIONS'])
    return preamble + ''.join(blocks[m[1]] for m in markers)
