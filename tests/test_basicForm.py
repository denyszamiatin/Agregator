from unittest import TestCase
from text_handler.basic_form import BasicForm


class TestBasicForm(TestCase):
    def test_convert_english_word(self):
        self.assertEqual(BasicForm.convert('go'), 'go')
        self.assertEqual(BasicForm.convert('went'), 'go')

    def test_convert_russian_word(self):
        self.assertEqual(BasicForm.convert('белки'), 'белка')

    def test_convert_ukrainian_word(self):
        self.assertEqual(BasicForm.convert('хати'), 'хата')


