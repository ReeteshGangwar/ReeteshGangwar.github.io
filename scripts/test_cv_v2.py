"""Protect the newer v2 layout and content while updating native records."""
import unittest
from datetime import date
from build_updates import ROOT, parse_updates
from build_cv_v2 import compile_v2, group, entries


class V2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (ROOT / '_content/cv-v2/cv-v2.tex').read_text()

    def apply(self, text):
        return compile_v2(self.base, parse_updates('```update\n' + text + '\n```\n'))

    def test_untouched_v2_is_preserved(self):
        expected = self.base.replace(r'Curriculum Vitae \textperiodcentered\ November 2026',
                                     r'Curriculum Vitae \textperiodcentered\ ' + date.today().strftime('%B %Y'))
        self.assertEqual(compile_v2(self.base, []), expected)

    def test_patent_summary_tracks_new_patents(self):
        result = self.apply('Type: Publication\nCategory: Patent\nTitle: NEW PATENT\nAuthors: Reetesh Kumar Gangwar\nJournal: Indian Patent Office\nYear: 2027')
        self.assertIn(r'\stat{3}{patent', result)

    def test_nested_tex_groups(self):
        self.assertEqual(group(r'{A \textbf{B \emph{C}}}', 0)[0], r'A \textbf{B \emph{C}}')

    def test_new_paper_keeps_v2_author_decorations(self):
        result = self.apply('Type: Publication\nTitle: NEW V2 PAPER\nAuthors: T. Pushparaj Gandhi, Reetesh Kumar Gangwar and A. Author\nJournal: Journal\nYear: 2027')
        self.assertIn(r'\stu{T. Pushparaj Gandhi}', result)
        self.assertIn(r'\me{}', result)
        self.assertIn('Publications, 2024 -- 2027', result)
        self.assertLess(result.index('Journal articles -- 2027'), result.index('Journal articles -- 2026'))

    def test_student_graduation_changes_counts_without_losing_others(self):
        result = self.apply('Type: Student\nName: Abhay Kumar\nProgramme: PhD\nStatus: Alumni\nTopic: Thesis\nYear: 2024\nEndYear: 2027')
        self.assertEqual(result.count('Abhay Kumar'), 1)
        self.assertIn(r'\stat{4\,+\,4}', result)
        self.assertIn('graduates (4)', result)
        self.assertIn('ongoing (4)', result)
        self.assertIn('Joint supervision with', result)

    def test_course_replacement_keeps_v2_table(self):
        result = self.apply('Type: Teaching\nCode: PH605L\nTitle: UPDATED COURSE\nLevel: Postgraduate\nSemesters: Jan–Jun 2027')
        self.assertEqual(result.count('PH605L &'), 1)
        self.assertIn('UPDATED COURSE', result)
        self.assertIn('PH105L &', result)
        self.assertIn(r'\begin{longtable}', result)

    def test_project_short_title_matches_agency_and_year(self):
        result = self.apply('Type: Project\nTitle: Full new wording of the NQM project\nAgency: DST\nRole: Co-PI\nYear: 2026\nEndYear: 2029\nStatus: Ongoing\nKind: Sponsored\nFunding: INR 70.64 lakh')
        self.assertNotIn('Quantum machine learning: Reservoir computing and PDE solvers', result)
        self.assertIn(r'\stat{\rs3.58 Cr}', result)
        self.assertIn('9 projects, PI on 5', result)

    def test_shared_student_table_is_preserved_on_ambiguous_update(self):
        with self.assertRaisesRegex(ValueError, 'shared student table'):
            self.apply('Type: Student\nName: Somya Pal\nProgramme: MTech\nStatus: Alumni\nTopic: Thesis')

    def test_memberships_and_updated_education_are_preserved(self):
        result = self.apply('Type: Award\nTitle: NEW HONOUR\nYear: 2027\nDetails: Institution')
        self.assertIn('NEW HONOUR', result)
        self.assertIn('No.\\ ROO/LM/12792', result)
        self.assertIn('Postdoctoral Researcher}, Universit', result)


if __name__ == '__main__':
    unittest.main()
