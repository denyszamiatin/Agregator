import glob
import itertools
import re
import reprlib
import string
from multiprocessing import Pool
from urllib.parse import urlparse

import chardet
import requests
import yaml
from bs4 import BeautifulSoup

VALID_URL_TEMPLATE = re.compile(
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F]'
    '[0-9a-fA-F]))+'
)


DICTIONARY_PATH = 'dictionaries'
UNDESIRABLE_PUNCTUATION = '»—▼▲≡©'
LANGUAGE = ('en', 'ru',)
POOL_NUMBER = 5


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


def url_to_dict(url):
    url = urlparse(url)
    d = {'r_path': ''}
    if url[0]:
        d['scheme'] = url[0]
    if url[1]:
        d['netloc'] = url[1]
    if url[2]:
        path = url[2] + '/' if not url[2].endswith('/') else url[2]
        if path.startswith('/'):
            d['path'] = path
        else:
            d['r_path'] = path
    return d


def dict_url_to_string(url):
    return '{scheme}://{netloc}{path}{r_path}'.format(**url)


def parse_config_file(file):
    with open(file, 'r') as config:
        configuration = yaml.load(config)
    return configuration


def decode_string(content):
    """Decode string to unicode string."""
    # charset = chardet.detect(data)['encoding']
    # try:
    #     return data.decode(charset)
    # except ValueError:
    #     return ''
    charset = chardet.detect(content)['encoding']
    return content.decode(charset)


def load_stop_words():
    """
    Initializes set of stop words
    """
    stop_words = set()

    for file in glob.glob('{}/*.txt'.format(DICTIONARY_PATH)):
        with open(file) as dictionary:
            stop_words.update(set(dictionary.read().splitlines()))
    return stop_words


def get_page(url):
    return Page(url)


def gen_page(urls):
    with Pool(POOL_NUMBER) as p:
        d = p.map(get_page, urls)
    return d


def com_page(couple_of_page):
    first, second = couple_of_page
    return first.compare_page(second)


def compare_page(pages):
    with Pool(POOL_NUMBER) as p:
        result = p.map(com_page, pages)
    return result


class Agregator:
    def __init__(self, config_file='config.yml'):
        config = parse_config_file(config_file)
        self.urls_need_check = {url for url in config['url'] if check_url(url)}
        self.requests = {Normalize.text(request) for request
                         in config['requests']}
        self.page_limit = config['page_limit']
        self.pages = []
        self.urls_check = set()
        self.walk()

    def walk(self):
        while True:
            delta = self.urls_need_check - self.urls_check
            if not delta or len(self.pages) == self.page_limit:
                break
            limit = self.page_limit - len(self.pages)
            part_of_urls = list(delta)[:limit]
            new_page = gen_page(part_of_urls)
            self.urls_check.update(set(part_of_urls))
            for page in new_page:
                if page:
                    self.urls_need_check.update(page.urls_on_page)
                    self.pages.append(page)

    def compare_pages(self):
        result = compare_page(list(itertools.combinations(self.pages, 2)))
        for report in result:
            print(report)


class Page:
    UNDESIRABLE_TAGS = ('script', 'style')

    def __init__(self, url):
        self._valid_page = True
        self._url = url
        self._parser = BeautifulSoup
        self._content, self._urls_on_page = self._parse_page()

    def _parse_page(self):
        decode_page = self._get_decode_content()
        if self._valid_page:
            soup = BeautifulSoup(decode_page, 'html.parser')
            self._remove_special_tags(soup)
            content = Normalize.text(' '.join(soup.get_text().split()))
            return content, self._get_urls_from_page(soup)
        else:
            return decode_page, set()

    def _get_decode_content(self):
        try:
            if requests.head(self._url).status_code == 200:
                return decode_string(requests.get(self._url).content)
            else:
                raise ValueError
        except (ValueError, requests.exceptions.RequestException):
            self._valid_page = False
            return ''

    def _remove_special_tags(self, soup):
        for block in soup(self.UNDESIRABLE_TAGS):
            block.extract()

    def _get_urls_from_page(self, soup):
        """Return list of URLs on HTML page"""
        urls = [a['href'] for a in soup.find_all('a', href=True)]
        return self._normalize_url(urls)

    def _normalize_url(self, urls):
        """
        >>> p = Page
        >>> p._url = 'http://itea.ua/courses-itea/python/python-advanced/'
        >>> p._normalize_url(p, urls=['/contacts/', 'http://itea.ua/premises-lease/', 'some_other_page'])
        {'http://itea.ua/premises-lease/', 'http://itea.ua/contacts/', 'http://itea.ua/courses-itea/python/python-advanced/some_other_page/'}
        """
        normalized_url = set()
        base_url_dict = url_to_dict(self._url)
        for url in urls:
            normalized_url.add(dict_url_to_string(
                dict(base_url_dict, **url_to_dict(url))))

        return {url for url in normalized_url if check_url(url)}

    def compare_page(self, other_page, shingle_length=10):
        other_url = other_page._url
        def get_hash(text):
            return [hash(section.encode()) for section in get_shingles(text)]

        def get_shingles(text):
            shingles = []
            s_text = text.split()
            for i in range(len(s_text) - (shingle_length - 1)):
                shingles.append(
                    ' '.join([x for x in s_text[i:i + shingle_length]]))
            return tuple(shingles)

        original = get_hash(self.text)
        other_page = get_hash(other_page.text)
        same = 0
        # same = len(set(original) & set(other_page))
        for shingle in original:
            if shingle in other_page:
                same += 1

        same * 2 / (float(len(original) + len(other_page))) * 100

        return 'Content from this web page {} repeat content from that ' \
               'web page {} by {}%.'.format(self._url, other_url, same)

    @property
    def text(self):
        return self._content

    @property
    def urls_on_page(self):
        return self._urls_on_page

    def __bool__(self):
        return self._valid_page

    def __repr__(self):
        return "{}('{}')".format(type(self.__name__), reprlib.repr(self._url))


class Normalize:
    stop_words = load_stop_words()
    unnecessary_char = {ord(char): ' ' for char in
                        (string.punctuation + '»—▼▲≡©')}

    @classmethod
    def text(cls, raw_text):
        """
        Return normalize text in lower case without: undesirable punctuation
        and stop words.
        >>> Normalize.text('Я только хотел сказать, что эти '\
        'стоп-слова — сложная штука.')
        'хотел стоп слова сложная штука'
        >>> Normalize.text('What are your goals?')
        'goals'
        """
        text = raw_text.translate(cls.unnecessary_char).lower()
        text = ' '.join([word for word in text.split() if word not in
                         cls.stop_words])
        return text


if __name__ == '__main__':
    a = Agregator()
    a.compare_pages()

