"""CV regression tests for replacement, safety and preservation of baseline data."""
import unittest
from pathlib import Path
import tempfile
import subprocess
from unittest.mock import patch
from build_cv import ROOT, build, compile_sections, remove_entry, tex


def section(name, content=''):
    return '\\begin{rubric}{' + name + '}\n' + content + '\\end{rubric}\n'


class CVTests(unittest.TestCase):
    def test_existing_publication_is_replaced_once(self):
        base = {'publications': section('Publications', '\\subrubric{Journal Articles -- 2026}\n\\entry*[] A, ``Existing paper'', Journal.\n')}
        records = [dict(type='publication', title='Existing paper', authors='B', journal='New journal', year='2026')]
        result = compile_sections(base, records)['publications']
        self.assertEqual(result.count('Existing paper'), 1)
        self.assertIn('New journal', result)
        self.assertEqual(base['publications'].count('New journal'), 0)

    def test_new_year_precedes_old_year(self):
        base = {'publications': section('Publications', '\\subrubric{Journal Articles -- 2026}\n\\entry*[] Old paper\n')}
        result = compile_sections(base, [dict(type='publication', title='New paper', authors='A', journal='J', year='2027')])['publications']
        self.assertLess(result.index('2027'), result.index('2026'))
        self.assertIn('Old paper', result)

    def test_student_graduation_moves_existing_record(self):
        base = {'scholars': section('Students', '\\subrubric{Ph.D. Scholars (ongoing)}\n\\entry*[2022] \\textbf{Mr.\\ A. Kumar} -- Old topic\n')}
        result = compile_sections(base, [dict(type='student', name='A. Kumar', programme='PhD', status='Alumni', topic='Thesis', year='2022', endyear='2026')])['scholars']
        self.assertEqual(result.count('A. Kumar'), 1)
        self.assertIn('Ph.D. Graduates', result)

    def test_project_same_title_different_category(self):
        base = {'projects': section('Projects', '\\entry*[] Total sanctioned: stale total\n\\subrubric{Sponsored Research Projects}\n\\entry*[2026] Same title\n\\subrubric{Consultancy Projects}\n\\entry*[2025] Same title\n')}
        record = dict(type='project', title='Same title', kind='Consultancy', agency='Company', role='PI', status='Completed', year='2025')
        result = compile_sections(base, [record])['projects']
        self.assertEqual(result.count('Same title'), 2)
        self.assertNotIn('stale total', result)

    def test_news_and_page_edits_do_not_become_cv_entries(self):
        base = {'service': section('Service', '\\entry*[] Existing role\n')}
        self.assertEqual(compile_sections(base, [dict(type='news'), dict(type='page'), dict(type='profile')]), base)

    def test_service_replaces_existing_title(self):
        base = {'service': section('Service', '\\subrubric{Service to the Scientific Community}\n\\entry*[2026] \\textbf{Editorial Board Member}, PSST\n')}
        result = compile_sections(base, [dict(type='service', title='Editorial Board Member', details='PSST', period='2026 -- present')])['service']
        self.assertEqual(result.count('Editorial Board Member'), 1)

    def test_ambiguous_identity_fails(self):
        with self.assertRaises(ValueError):
            remove_entry(section('S', '\\entry*[] A Kumar\n\\entry*[] A Kumar\n'), 'A Kumar')

    def test_user_tex_is_escaped(self):
        value = tex(r'50% & x_1 $ {test} \input{secret}')
        self.assertIn(r'50\% \& x\_1 \$', value)
        self.assertIn(r'\textbackslash{}input\{secret\}', value)

    def test_missing_removal_fails(self):
        with self.assertRaises(ValueError):
            compile_sections({'awards': section('Awards')}, [dict(type='award', title='Unknown', action='remove')])

    def test_compiler_failure_preserves_served_pdf(self):
        archive = ROOT / 'archive'
        archive.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=archive) as folder:
            folder = Path(folder)
            served = folder / 'existing.pdf'
            served.write_bytes(b'%PDF-original')
            with patch('build_cv.shutil.which', return_value='/unused/tectonic'), patch(
                'build_cv.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'tectonic')
            ), self.assertRaises(subprocess.CalledProcessError):
                build(work=folder / 'work', destination=served)
            self.assertEqual(served.read_bytes(), b'%PDF-original')
            self.assertFalse(served.with_suffix('.pdf.tmp').exists())

    def test_real_appointment_and_paper_are_not_duplicated(self):
        from build_cv import SECTIONS
        from build_updates import parse_updates, compile_pages
        base = {name: (ROOT / '_content/cv' / (name + '.tex')).read_text() for name in SECTIONS}
        records = parse_updates('''```update
Type: Publication
Title: Synergistic falling film nonthermal plasma and UV-photon hybrid system: An advanced and energy-efficient approach for rapid dye degradation
Authors: Test authors
Journal: Separation and Purification Technology
Year: 2026
Announce: Yes
Date: 2026-11-06
```
```update
Type: Service
Title: Editorial Board Member, Plasma Sources Science and Technology
Period: October 2026–present
Details: Plasma Sources Science and Technology (IOP Publishing)
```
```update
Type: News
Title: Editorial Board appointment at Plasma Sources Science and Technology
Date: 2026-11-06
Details: Appointed Editorial Board Member.
```
''')
        result = compile_sections(base, records)
        self.assertEqual(result['service'].count('Editorial Board Member'), 1)
        self.assertIn('Guest Editor', result['service'])
        self.assertEqual(result['publications'].count('Synergistic falling film'), 1)
        pages = compile_pages({p.stem:p.read_text() for p in (ROOT / '_content/base').glob('*.qmd')}, records)
        self.assertEqual(pages['service'].count('Editorial Board Member'), 1)
        self.assertIn('Guest Editor', pages['service'])
        self.assertIn('Synergistic falling film', pages['_latest-updates'])
        self.assertIn('Editorial Board appointment', pages['_latest-updates'])


if __name__ == '__main__':
    unittest.main()
