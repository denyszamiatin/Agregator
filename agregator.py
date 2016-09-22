import binascii
import os.path
import re
import string
from collections import OrderedDict
from urllib.parse import urlparse

import chardet
import requests
from bs4 import BeautifulSoup

VALID_URL_TEMPLATE = re.compile(
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F]'
    '[0-9a-fA-F]))+'
)


class AgregatorError(Exception):
    pass


def check_url(url):
    """
    Check url by regex VALID_URL_TEMPLATE.
    >>> check_url('http://itea.ua/courses-itea/python/python-advanced/')
    True
    >>> check_url('https://www.fullstackpython.com/best-python-resources.html')
    True
    >>> check_url('Python')
    False
    >>> check_url(None)
    False
    """
    return bool(url and VALID_URL_TEMPLATE.fullmatch(url))


def get_url_list_from_file(file_path='urls.txt'): # TODO - this function may be a method of Spider
    """
    Open file and return urls.txt of valid urls.txt.
    >>> get_url_list_from_file(file_path='./tests/only_urls.txt')
    ['http://itea.ua/courses-itea/python/python-advanced/', \
'https://www.fullstackpython.com/best-python-resources.html', \
'https://pymotw.com/3/', \
'https://www.python.org/dev/peps/pep-0020/']
    >>> get_url_list_from_file(file_path='./tests/mix_text_urls.txt')
    ['http://itea.ua/courses-itea/python/python-advanced/', \
'https://www.fullstackpython.com/best-python-resources.html', \
'https://pymotw.com/3/', \
'https://www.python.org/dev/peps/pep-0020/']
    >>> get_url_list_from_file(file_path='./tests/text_without_url.txt')
    Traceback (most recent call last):
    ...
    agregator.AgregatorError: No url in set file
    >>> get_url_list_from_file(file_path='abrakadabra.txt')
    Traceback (most recent call last):
    ...
    agregator.AgregatorError: File not found

    """
    try:
        with open(os.path.normpath(file_path), 'r') as f:
            url_file = f.read()
    except FileNotFoundError:
        raise AgregatorError('File not found')
    url_list = [url for url in url_file.split() if check_url(url)]
    if not url_list:
        raise AgregatorError('No url in set file')
    return url_list


class URLParser:
    UNDESIRABLE_TAGS = ('script', 'style')

    def __init__(self, url, parser=BeautifulSoup):
        self._url = url
        self._parser = parser
        self._raw_page = self.decode_page(self.get_content())
        self._parsed_page = self._parser(self._raw_page, 'html.parser')
        self._remove_special_tags()
        self._text = self._get_pure_text()
        self._urls = self._get_urls_from_page()

    @property
    def text(self):
        return self._text

    @property
    def urls_on_page(self):
        return self._urls

    def get_content(self):
        """ Get web page in bytes format by url. If something wrong return None """
        try:
            if requests.head(self._url).status_code == 200:
                return requests.get(self._url).content
            else:
                return None
        except requests.exceptions.RequestException:
            return None

    @staticmethod
    def decode_page(data):
        charset = chardet.detect(data)['encoding']
        try:
            return data.decode(charset)
        except ValueError:
            return ''

    def _remove_special_tags(self):
        """Completely remove script or style or any other special tags."""
        for un_t in self._parsed_page(self.UNDESIRABLE_TAGS):
            un_t.extract()

    def _get_pure_text(self):
        """Remove multiple white spaces"""
        return ' '.join(self._parsed_page.get_text().split())

    def _get_urls_from_page(self):
        """Return list of URLs on HTML page"""
        urls = [a['href'] for a in self._parsed_page.find_all('a', href=True)]
        return self._normalize_urls(urls)

    def _normalize_urls(self, urls):
        scheme, domain, url, *tail = urlparse(self._url)
        normalized_url = []
        for current_url in urls:
            if current_url:
                domain_in_current_url = urlparse(current_url)[1]
                if domain_in_current_url == domain:
                    normalized_url.append(current_url)
                elif domain_in_current_url == '':
                    # Does url from root or from this page
                    if current_url.startswith('/'):
                        normalized_url.append("{0}://{1}{2}".format(scheme, domain, current_url))
                    else:
                        normalized_url.append("{0}://{1}{2}{3}".format(scheme, domain, url, current_url))
        return {clean_url for clean_url in normalized_url if check_url(clean_url)}


class NormalizeText:
    def __init__(self, dictionary_path='dictionaries',
                 undesirable_punctuation='»—▼▲≡©',
                 language=tuple()):
        self.dictionary_path = dictionary_path
        self.language = language
        self.stop_words = self.load_stop_words()
        self.undesirable_punctuation = {ord(char):' ' for char in
             (string.punctuation + undesirable_punctuation)}

    def load_stop_words(self):
        """
        Initializes set of stop words(from files in folder)
        """
        stop_words = set()

        def update_set(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                stop_words.update(set(f.read().splitlines()))

        test_lang = lambda name: name.startswith(self.language)\
            if self.language else lambda x: True
        for root, dirs, files in os.walk(self.dictionary_path):
            for name in files:
                if test_lang(name):
                    update_set(os.path.join(root, name))

        return stop_words

    def normalize(self, raw_text):
        """
        Return normalize text in lower case without: undesirable punctuation
        and stop words.
        >>> normalize = NormalizeText()
        >>> normalize.normalize('Я только хотел сказать, что эти стоп-слова '\
        '— сложная штука.')
        'хотел стоп слова сложная штука'
        >>> normalize.normalize('What are your goals?')
        'goals'
        """
        text = raw_text.translate(self.undesirable_punctuation).lower()
        text = ' '.join([word for word in text.split() if not word in
                                                              self.stop_words])
        return text


class ComparingText:
    """Comparing two text"""
    _hash_method = OrderedDict({'hash': hash, 'binascii.crc32': binascii.crc32})

    def __init__(self, text1, text2, shingle_length=10):
        self._shingle_length = shingle_length
        self.text1 = text1
        self.text2 = text2

        self._shingle_text1 = self.get_shingles(text1)
        self._shingle_text2 = self.get_shingles(text2)

        self.hash_text1 = self.get_hash(self._shingle_text1)
        self.hash_text2 = self.get_hash(self._shingle_text2)

    def get_shingles(self, text):
        shingles = []
        s_text = text.split()
        for i in range(len(s_text) - (self._shingle_length - 1)):
            shingles.append(' '.join([x for x in s_text[i:i+self._shingle_length]]))
        return tuple(shingles)

    def get_hash(self, shingle):
        hash_array = []
        for method in self._hash_method.values():
            hash_array.append([method(section.encode()) for section in shingle])
        return hash_array

    def compare(self):
        same = 0
        if len(self.hash_text1[0]) >= len(self.hash_text2[0]):
            text_a, text_b = self.hash_text1, self.hash_text2
        else:
            text_b, text_a = self.hash_text1, self.hash_text2
        min_size = len(text_b[0])
        for i in range(len(self._hash_method)):
            for j in range(min_size):
                if text_b[i][j] in text_a[i]:
                    same += 1
        return same * 2 / (float(len(text_a[0]) + len(text_b[0]))*len(self._hash_method)) * 100


def controller(page):
    """
    Controller  spider which parse pages and return list url and text

    """
    print(page)
    level_url = set()
    level_url_get = {page}
    map_page_content = {}
    normalize = NormalizeText()
    while True:
        url_check = level_url_get - level_url
        if not url_check:
            break
        for url in url_check:
            print(url)
            level_url.add(url)
            page = URLParser(url)                                # use class URLParser
            normalize_page = normalize.normalize(page.text)
            map_page_content[url] = normalize_page
            level_url_get.update(page.urls_on_page)
            print('len=',len(level_url_get))
            print ("delta len = ", len(level_url_get)-len(level_url))

    print(map_page_content)
    return map_page_content


def get_base_form_of_words(text, lag):
    pass

if __name__ == '__main__':
    normalize = NormalizeText()
    text = []
    for url in get_url_list_from_file('urls.txt'):
        page = URLParser(url)
        url_list = page.urls_on_page
        normalize_page = normalize.normalize(page.text)
        debug = True
        print(page.text)
        print(normalize_page)
        text.append(normalize_page)
        print(url_list)

    comparing = ComparingText(text[0], text[1]).compare()
    print(comparing)
