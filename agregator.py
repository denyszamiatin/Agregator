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

def get_url_list_from_file(file_path='urls.txt'):
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


def get_content(url):
    """
    Get web page in bytes format by url. If something wrong return None
    >>> type(get_content(url='http://itea.ua/courses-itea/python/python-advanced/'))
    <class 'bytes'>
    >>> type(get_content('hts://pysad2asdmotw.com/3/'))
    <class 'NoneType'>
    """
    try:
        if requests.head(url).status_code == 200:
            return requests.get(url).content
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def decode(data):
    """Decode raw data to unicode string."""
    charset = chardet.detect(data)['encoding']
    try:
        return data.decode(charset)
    except ValueError:
        return ''


def remove_special_tags(soup, tags):
    """Completely remove script or style or any other special tags."""
    for script in soup(tags):
        script.extract()
    return soup


def remove_multiple_white_spaces(text):
    """Remove multiple white spaces"""
    return ' '.join(text.split())


def remove_html_tags(page):
    """Remove HTML tags and remove."""
    soup = BeautifulSoup(page, 'html.parser')
    remove_special_tags(soup, ["script", "style"])
    return remove_multiple_white_spaces(soup.get_text())


def validate_domain_in_url(scheme, domain, url):
    """Return absolute url if domain in url or url is relative another return none"""
    if url:
        url_domain = urlparse(url)[1]
        if url_domain == domain:
            return url
        elif url_domain == '':
            return "{0}://{1}{3}{2}".format(
                scheme, domain, url, ('/' if url[0] != '/' else '')
            )
    return None


def get_urls_from_page(page, current_url):
    """Return list of URLs on HTML page"""
    soup = BeautifulSoup(page, 'html.parser')
    remove_special_tags(soup, ["script", "style"])
    urls = [a['href'] for a in soup.find_all('a', href=True)]
    scheme, domain, *tail = urlparse(current_url)
    clean_url = [validate_domain_in_url(scheme, domain, url) for url in urls]
    return {a for a in clean_url if check_url(a)}


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
            with open(file_path, 'r') as f:
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
            hash_array.append([])
            for section in shingle:
                hash_array[-1].append(method(section.encode()))
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


if __name__ == '__main__':
    normalize = NormalizeText()
    text = []
    for url in get_url_list_from_file('urls.txt'):
        page = get_content(url)
        decode_page = decode(page)
        page_without_tags = remove_html_tags(decode_page)
        url_list = get_urls_from_page(decode_page, url)
        normalize_page = normalize.normalize(page_without_tags)
        debug = True
        print(page_without_tags)
        print(normalize_page)
        print(url_list)
