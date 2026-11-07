"""Content routing and failure tests. Examples never write to the live source pages."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from build_updates import ROOT, parse_updates, compile_pages, build, ROW

class Updates(unittest.TestCase):
 def setUp(self):
  compiler=patch('build_cv.build');compiler.start();self.addCleanup(compiler.stop)
 @classmethod
 def setUpClass(cls):cls.base={f.stem:f.read_text() for f in (ROOT/'_content/base').glob('*.qmd')}
 def compile(self,text):return compile_pages(self.base,parse_updates(text))
 def block(self,body):return '```update\n'+body+'\n```\n'
 def test_instruction_examples_are_not_published(self):
  document=(ROOT/'UPDATE-WEBSITE.md').read_text()
  examples=document.split('## Examples',1)[1]
  self.assertIn('```example',examples)
  self.assertEqual(parse_updates(examples),[])
  pages=self.compile(document)
  self.assertNotIn('Your announcement title',pages['_news-archive'])
  self.assertNotIn('Full paper title',pages['publications'])
 def test_publication_routes_to_new_year_and_optional_news(self):
  pages=self.compile(self.block('Type: Publication\nTitle: TEST-ONLY plasma paper\nAuthors: A. Author\nJournal: Test Journal\nYear: 2027\nDOI: 10.1234/test\nAnnounce: Yes\nDate: 2027-02-15'))
  self.assertIn('## Journal Articles – 2027',pages['publications'])
  self.assertLess(pages['publications'].index('2027'),pages['publications'].index('## Journal Articles – 2026'))
  self.assertIn('TEST-ONLY plasma paper',pages['_latest-updates'])
  self.assertIn('https://doi.org/10.1234/test',pages['publications'])
 def test_same_publication_is_not_duplicated(self):
  one='Type: Publication\nTitle: TEST-ONLY same paper\nAuthors: A. Author\nJournal: Journal\nYear: 2027'
  pages=self.compile(self.block(one)+self.block(one.replace('Journal: Journal','Journal: Revised Journal')))
  self.assertEqual(pages['publications'].count('TEST-ONLY same paper'),1)
  self.assertIn('*Revised Journal*',pages['publications'])
 def test_publication_matches_existing_style(self):
  pages=self.compile(self.block('Type: Publication\nTitle: TEST-ONLY styled paper\nAuthors: A. Student and Reetesh Kumar Gangwar\nJournal: Test Journal\nYear: 2027\nDOI: 10.1234/style\nDetails: TEST-ONLY announcement sentence'))
  self.assertIn('A. Student and **R. K. Gangwar**, “TEST-ONLY styled paper”, *Test Journal* (2027). [DOI](https://doi.org/10.1234/style)',pages['publications'])
  self.assertNotIn('TEST-ONLY announcement sentence',pages['publications'])
 def test_current_student_moves_to_alumni(self):
  pages=self.compile(self.block('Type: Student\nName: Abhay Kumar\nProgramme: PhD\nStatus: Alumni\nTopic: Plasma-based wastewater treatment\nYear: 2024\nEndYear: 2027\nPosition: TEST-ONLY next position'))
  name_at=pages['group'].index('**Abhay Kumar**')
  self.assertGreater(name_at,pages['group'].index('## Ph.D. Graduates'))
  self.assertNotIn('**Mr. Abhay Kumar**',pages['group'])
 def test_new_student_is_routed_to_group_only(self):
  pages=self.compile(self.block('Type: Student\nName: TEST-ONLY Student\nProgramme: PhD\nStatus: Current\nTopic: Plasma theory\nYear: 2027'))
  self.assertIn('TEST-ONLY Student',pages['group'])
  self.assertNotIn('TEST-ONLY Student',pages['_latest-updates'])
 def test_talk_routes_to_year_and_category(self):
  pages=self.compile(self.block('Type: Talk\nTitle: TEST-ONLY training\nDate: 2026-10-19\nEvent: Test institution\nKind: FDP lecture'))
  where=pages['talks'].index('TEST-ONLY training')
  self.assertGreater(where,pages['talks'].index('### FDP, training & popular talks'))
  self.assertLess(where,pages['talks'].index('## 2025'))
 def test_project_routes_to_consultancy(self):
  pages=self.compile(self.block('Type: Project\nTitle: TEST-ONLY consultancy\nAgency: Test company\nRole: PI\nYear: 2027\nStatus: Ongoing\nKind: Consultancy'))
  self.assertGreater(pages['projects'].index('TEST-ONLY consultancy'),pages['projects'].index('## Consultancy Projects'))
 def test_teaching_replaces_course_by_code(self):
  pages=self.compile(self.block('Type: Teaching\nCode: PH605L\nTitle: Basics and Applications of Plasma Physics\nLevel: Postgraduate\nSemesters: Jul–Dec 2027, Jul–Dec 2026'))
  self.assertEqual(sum('PH605L' in m[1] for m in ROW.finditer(pages['teaching'])),1)
  self.assertIn('Jul–Dec 2027',pages['teaching'])
 def test_homepage_intro_can_be_replaced(self):
  pages=self.compile(self.block('Type: Profile\nField: research-introduction\nText: TEST-ONLY replacement introduction.'))
  self.assertIn('TEST-ONLY replacement introduction.',pages['index'])
  self.assertNotIn('My research lies at the interface',pages['index'])
 def test_news_feed_is_limited_but_archive_is_complete(self):
  blocks=''.join(self.block(f'Type: News\nTitle: TEST-ONLY news {i}\nDate: 2027-01-{i:02d}\nDetails: News detail.') for i in range(1,8))
  pages=self.compile(blocks)
  self.assertEqual(pages['_latest-updates'].count('### '),5)
  self.assertEqual(pages['_news-archive'].count('TEST-ONLY news'),7)
  self.assertLess(pages['_latest-updates'].index('news 7'),pages['_latest-updates'].index('news 6'))
  self.assertNotIn('news 1',pages['_latest-updates'])
 def test_exact_wording_update(self):
  pages=self.compile(self.block('Type: Page\nPage: research\nFind: My research connects microscopic collision processes\nReplace: My work connects microscopic collision processes'))
  self.assertIn('My work connects microscopic',pages['research'])
 def test_remove_existing_student(self):
  pages=self.compile(self.block('Type: Student\nName: Abhay Kumar\nAction: Remove'))
  self.assertNotIn('**Mr. Abhay Kumar**',pages['group'])
 def test_invalid_fields_dates_and_photo_paths_fail(self):
  bad=['Type: News\nTitle: Missing details\nDate: 2027-01-01',
       'Type: News\nTitle: Bad date\nDate: 2027-02-31\nDetails: Detail',
       'Type: News\nTitle: Bad URL\nDate: 2027-01-01\nDetails: Detail\nURL: javascript:alert(1)',
       'Type: Student\nName: TEST-ONLY\nProgramme: PhD\nStatus: Current\nTopic: Test\nPhoto: ../outside.jpg',
       'Type: Student\nName: TEST-ONLY\nProgramme: PhD\nStatus: Current\nTopic: Test\nPhoto: assets/missing.jpg',
       'Type: News\nTitle: Typo\nDate: 2027-01-01\nDetails: Detail\nAnounce: Yes']
  for text in bad:
   with self.subTest(text=text),self.assertRaises(ValueError):self.compile(self.block(text))
 def test_invalid_update_does_not_modify_pages(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'_content/base').mkdir(parents=True)
   for name,text in self.base.items():(root/'_content/base'/(name+'.qmd')).write_text(text)
   (root/'index.qmd').write_text('UNCHANGED')
   (root/'UPDATE-WEBSITE.md').write_text(self.block('Type: News\nTitle: Invalid'))
   with self.assertRaises(ValueError):build(root)
   self.assertEqual((root/'index.qmd').read_text(),'UNCHANGED')
 def test_build_is_repeatable(self):
  text=self.block('Type: News\nTitle: TEST-ONLY repeatable\nDate: 2027-01-01\nDetails: Detail')
  self.assertEqual(self.compile(text),self.compile(text))

if __name__=='__main__':unittest.main()
