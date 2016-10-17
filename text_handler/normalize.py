import string
import glob
from text_handler.basic_form import convert


DICTIONARY_PATH = 'dictionaries'
UNDESIRABLE_PUNCTUATION = '»—▼▲≡©'


def load_stop_words():
    """
    Initializes set of stop words
    """
    stop_words = set()

    for file in glob.glob('{}/*.txt'.format(DICTIONARY_PATH)):
        with open(file) as dictionary:
            stop_words.update(set(dictionary.read().splitlines()))
    return stop_words


class Normalize:
    stop_words = load_stop_words()
    unnecessary_char = {ord(char): ' ' for char in
                        (string.punctuation + '»—▼▲≡©')}

    @classmethod
    def text(cls, raw_text):
        text = raw_text.translate(cls.unnecessary_char).lower()
        text = ' '.join([convert(word) for word in text.split()
                         if word not in cls.stop_words])
        return text