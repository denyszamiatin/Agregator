import reprlib
from multiprocessing import Pool

import requests
from bs4 import BeautifulSoup

from model.mongo import MongoDBConnection, DuplicateKeyError
from text_handler.decode_text import decode_text
from text_handler.normalize import Normalize
from url_handler.urleee import url_to_dict, dict_url_to_string, check_url

POOL_NUMBER = 2


def _get_page(url):
    return Page(url)


def get_page(urls):
    with Pool(POOL_NUMBER) as p:
        d = p.map(_get_page, urls)
    return d


def compare_two_pages(couple_of_page):
    first, second = couple_of_page
    return first.compare_page(second)


def compare_page(pages):
    with Pool(POOL_NUMBER) as p:
        result = p.map(compare_two_pages, pages)
    return result


class Page:
    UNDESIRABLE_TAGS = ('script', 'style')

    def __init__(self, url):
        self._valid_page = True
        self._parser = BeautifulSoup
        self._url = url
        self._content, self._urls_on_page = self.cache()

    def cache(self):
        with MongoDBConnection() as mongo:
            page = mongo.connection.test.agregator.find_one({'_id': self.url})
            if page is None:
                content, urls_on_page = self._parse_page()
                try:
                    page = mongo.connection.test.agregator.insert(
                        {'_id': self.url,
                         'content': content,
                         'urls_on_page': list(urls_on_page)})
                    return content, urls_on_page
                except DuplicateKeyError:
                    self.cache()
            return page['content'], set(page['urls_on_page'])

    @property
    def url(self):
        return self._url

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
                return decode_text(requests.get(self._url).content)
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
        for shingle in original:
            if shingle in other_page:
                same += 1

        index = same * 2 / (float(len(original) + len(other_page))) * 100

        return 'Content from this web page {} repeat content from that ' \
               'web page {} by {}%.'.format(self._url, other_url, index)

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
