import unittest
import htmldeleate


class BasicTest(unittest.TestCase):
    def setUp(self):
        with open('html.test', 'rt') as f:
            self.html_doc = f.read()
        with open('regular.test', 'rt') as f:
            self.regular_text = f.read()
        self.regular_tags = {'h2': [' This is a H2 '], 'h3': [' This is a H3 '], 'h1': [' This is a H1 '],
                             'h5': [' This is a Broken H1\n    ...'], 'title': ["The Dormouse's story"]}

    def test_html_parse(self):
        txt = htmldeleate.get_text(self.html_doc)
        self.assertEqual(txt, self.regular_text)

    def test_get_html_tags(self):
        txt, cnt = htmldeleate.get_text(self.html_doc, ['h1', 'h3', 'h2', 'h5', 'title'])
        self.assertEqual(cnt, self.regular_tags)

    def test_raise_exeption(self):
        with self.assertRaises(TypeError):
            htmldeleate.get_text(self.html_doc, bytearray(['h1', 'h3', 'h2', 'h5', 'title']))

if __name__ == '__main__':
    unittest.main()
