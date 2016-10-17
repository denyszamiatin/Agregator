from unittest import TestCase
from text_handler.basic_form import convert


class TestBasicForm(TestCase):
    def test_convert_english_word(self):
        self.assertEqual(convert('go'), 'go')
        self.assertEqual(convert('went'), 'go')

    def test_convert_russian_word(self):
        self.assertEqual(convert('белки'), 'белка')

    def test_convert_ukrainian_word(self):
        self.assertEqual(convert('хати'), 'хата')


