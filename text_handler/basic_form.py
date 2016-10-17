import hunspell
import os


class BasicForm:
    original = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    en = hunspell.HunSpell(
        'dictionaries/en_GB.dic',
        'dictionaries/en_GB.aff')

    ua = hunspell.HunSpell(
        'dictionaries/uk_UA.dic',
        'dictionaries/uk_UA.aff')

    ru = hunspell.HunSpell(
        'dictionaries/ru_RU.dic',
        'dictionaries/ru_RU.aff')

    os.chdir(original)

    @classmethod
    def convert(cls, word):
        for lang in (cls.en, cls.ru, cls.ua):
            try:
                try:
                    return lang.stem(word)[0].decode('UTF-8')
                except UnicodeEncodeError:
                    # 'charmap' codec can't encode character u'\u0456'
                    return word
            except UnicodeDecodeError:
                return lang.stem(word)[0].decode('KOI8-R')
            except IndexError:
                continue
        return word

